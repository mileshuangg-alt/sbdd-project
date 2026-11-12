import json
import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest import mock

import numpy as np

from admet.qualification.datasail_scaling import probe, probe_p1


class DataSAILScalingProbeTests(unittest.TestCase):
    def test_fixture_is_deterministic(self):
        left = probe.deterministic_fixture(8)
        right = probe.deterministic_fixture(8)

        self.assertEqual(left.clusters, right.clusters)
        self.assertEqual(left.weights, right.weights)
        self.assertEqual(left.endpoint_counts, right.endpoint_counts)
        np.testing.assert_array_equal(left.s_matrix, right.s_matrix)
        np.testing.assert_array_equal(left.similarities, right.similarities)

    def test_numeric_endpoint_preservation_and_class_order(self):
        fixture = probe.deterministic_fixture(5)
        probe.assert_numeric_counts_preserved(fixture)

        broken = probe.SyntheticFixture(
            clusters=fixture.clusters,
            weights=fixture.weights,
            s_matrix=fixture.s_matrix[:, ::-1],
            similarities=fixture.similarities,
            endpoint_counts=fixture.endpoint_counts,
            classes=fixture.classes,
        )
        with self.assertRaises(AssertionError):
            probe.assert_numeric_counts_preserved(broken)

    def test_pinned_epsilon_and_stratification_semantics(self):
        fixture = probe.deterministic_fixture(4)
        self.assertEqual(probe.compute_limits(0.05, sum(fixture.weights), probe.STAGE_A_SPLITS), [13, 3])

        expected = np.array(
            [[sum(fixture.endpoint_counts["pKa"]) * 0.8 * 0.95, sum(fixture.endpoint_counts["clearance"]) * 0.8 * 0.95],
             [sum(fixture.endpoint_counts["pKa"]) * 0.2 * 0.95, sum(fixture.endpoint_counts["clearance"]) * 0.2 * 0.95]]
        )
        np.testing.assert_array_equal(probe.stratification_lower_bounds(fixture.s_matrix, probe.STAGE_A_SPLITS, 0.05), expected)

    def test_pair_and_assignment_variable_counts(self):
        self.assertEqual(probe.pair_term_count(6), 15)
        self.assertEqual(probe.pair_term_count(1), 0)

        try:
            fixture = probe.deterministic_fixture(4)
            problem, _, dimensions = probe.build_pinned_solve_c1_problem(
                fixture.clusters,
                fixture.weights,
                fixture.s_matrix,
                fixture.similarities,
                None,
                probe.DELTA,
                probe.EPSILON,
                probe.STAGE_A_SPLITS,
            )
        except ModuleNotFoundError as exc:
            self.skipTest(f"dependency unavailable: {exc}")

        self.assertIsNotNone(problem)
        self.assertEqual(dimensions["boolean_assignment_variables"], 8)
        self.assertEqual(dimensions["pair_terms"], 6)

    def test_small_n_objective_correctness(self):
        weights = [2.0, 3.0, 5.0]
        similarities = np.array([[1.0, 0.2, 0.4], [0.2, 1.0, 0.6], [0.4, 0.6, 1.0]])
        self.assertAlmostEqual(
            probe.small_objective_reference(weights, similarities, [0, 0, 1], 2),
            2.0 * 5.0 * 0.4 + 3.0 * 5.0 * 0.6,
        )

    def test_phase_gating_failure_stops_escalation(self):
        with tempfile.TemporaryDirectory() as directory:
            out = Path(directory)
            with mock.patch.object(probe, "validate_runtime_dependencies"), mock.patch.object(
                probe, "run_scenario", side_effect=[{"scenario": 100, "status": "failed", "stop_reason": "phase_timeout"}]
            ) as run_mock:
                code = probe.main(["--output-dir", str(out), "--scenarios", "100"])

        self.assertEqual(code, 1)
        run_mock.assert_called_once_with(100, out)

    def test_stage_specific_split_plans(self):
        stage_a = probe.split_plan_for_scenario(5446)
        stage_b = probe.split_plan_for_scenario(probe.STAGE_B_SCENARIO)

        self.assertEqual(stage_a.stage, "A")
        self.assertEqual(stage_a.names, ("dev", "test"))
        self.assertEqual(stage_a.ratios, (0.8, 0.2))
        self.assertEqual(stage_b.stage, "B5")
        self.assertEqual(stage_b.ratios, (0.2, 0.2, 0.2, 0.2, 0.2))

    def test_phase_monitor_uses_current_rss_samples(self):
        values = iter([100, 150, 125])
        with mock.patch.object(probe, "current_rss_bytes", side_effect=lambda: next(values)):
            monitor = probe.PhaseMonitor("test", 600)
            monitor.start_time = 0.0
            monitor.samples = []
            with mock.patch.object(probe.time, "monotonic", return_value=1.0):
                monitor._sample()
            with mock.patch.object(probe.time, "monotonic", return_value=2.0):
                monitor._sample()
            with mock.patch.object(probe.time, "monotonic", return_value=3.0):
                monitor._sample()

        self.assertEqual(monitor.peak_rss_bytes, 150)
        self.assertEqual([sample["rss_bytes"] for sample in monitor.samples], [100, 150, 125])

    def test_external_watchdog_terminates_on_rss_cap(self):
        class FakeProcess:
            pid = 12345
            exitcode = None

            def __init__(self):
                self.calls = 0

            def is_alive(self):
                self.calls += 1
                return self.calls == 1

        with tempfile.TemporaryDirectory() as directory, mock.patch.object(
            probe, "process_current_rss_bytes", return_value=probe.RSS_CAP_BYTES + 1
        ), mock.patch.object(probe, "terminate_process_group") as terminate_mock:
            record = probe.monitor_scenario_process(FakeProcess(), Path(directory))

        self.assertEqual(record["stop_reason"], "rss_cap_exceeded")
        terminate_mock.assert_called_once_with(12345)

    def test_phase_c_solver_limit_and_external_cap_are_distinct(self):
        self.assertEqual(probe.SOLVER_OPTIMIZATION_LIMIT_SECONDS, 1800)
        self.assertEqual(probe.SOLVE_EXTERNAL_PROCESS_CAP_SECONDS, 1860)
        self.assertEqual(probe.SCIP_PARAMS["limits/time"], 1800)
        self.assertEqual(probe.PHASE_CAPS_SECONDS["solve"], 1860.0)

        monitor = probe.PhaseMonitor("solve", probe.PHASE_CAPS_SECONDS["solve"])
        record = monitor.as_record()
        self.assertEqual(record["solver_optimization_limit_seconds"], 1800)
        self.assertEqual(record["external_process_cap_seconds"], 1860)

    def test_p1_wrapper_configures_only_p1_limits_and_authorization(self):
        snapshot = {
            "AUTHORIZED_CHARACTERIZATION_SCENARIOS": probe.AUTHORIZED_CHARACTERIZATION_SCENARIOS,
            "SOLVER_OPTIMIZATION_LIMIT_SECONDS": probe.SOLVER_OPTIMIZATION_LIMIT_SECONDS,
            "SOLVE_EXTERNAL_PROCESS_CAP_SECONDS": probe.SOLVE_EXTERNAL_PROCESS_CAP_SECONDS,
            "PHASE_CAPS_SECONDS": dict(probe.PHASE_CAPS_SECONDS),
            "SCIP_PARAMS": dict(probe.SCIP_PARAMS),
        }
        fixture_before = probe.deterministic_fixture(5)
        try:
            probe_p1.apply_p1_configuration(probe)

            self.assertEqual(probe.AUTHORIZED_CHARACTERIZATION_SCENARIOS, (500,))
            self.assertEqual(probe.SOLVER_OPTIMIZATION_LIMIT_SECONDS, 600)
            self.assertEqual(probe.SOLVE_EXTERNAL_PROCESS_CAP_SECONDS, 660)
            self.assertEqual(probe.SCIP_PARAMS["limits/time"], 600)
            self.assertEqual(probe.PHASE_CAPS_SECONDS["construction"], 600.0)
            self.assertEqual(probe.PHASE_CAPS_SECONDS["canonicalization"], 600.0)
            self.assertEqual(probe.PHASE_CAPS_SECONDS["solve"], 660.0)
            self.assertEqual(probe.parse_args(["--output-dir", "out"]).scenarios, [500])
            probe.validate_authorized_scenarios([500])
            with self.assertRaises(ValueError):
                probe.validate_authorized_scenarios([100])
            with self.assertRaises(ValueError):
                probe.validate_authorized_scenarios([1000])

            fixture_after = probe.deterministic_fixture(5)
            self.assertEqual(fixture_before.clusters, fixture_after.clusters)
            self.assertEqual(fixture_before.weights, fixture_after.weights)
            np.testing.assert_array_equal(fixture_before.s_matrix, fixture_after.s_matrix)
            np.testing.assert_array_equal(fixture_before.similarities, fixture_after.similarities)
            self.assertIs(probe_p1.probe.build_pinned_solve_c1_problem, probe.build_pinned_solve_c1_problem)
        finally:
            probe.AUTHORIZED_CHARACTERIZATION_SCENARIOS = snapshot["AUTHORIZED_CHARACTERIZATION_SCENARIOS"]
            probe.SOLVER_OPTIMIZATION_LIMIT_SECONDS = snapshot["SOLVER_OPTIMIZATION_LIMIT_SECONDS"]
            probe.SOLVE_EXTERNAL_PROCESS_CAP_SECONDS = snapshot["SOLVE_EXTERNAL_PROCESS_CAP_SECONDS"]
            probe.PHASE_CAPS_SECONDS = snapshot["PHASE_CAPS_SECONDS"]
            probe.SCIP_PARAMS = snapshot["SCIP_PARAMS"]

    def test_p0_configuration_remains_unchanged_after_p1_test_restore(self):
        self.assertEqual(probe.AUTHORIZED_CHARACTERIZATION_SCENARIOS, (100,))
        self.assertEqual(probe.SOLVER_OPTIMIZATION_LIMIT_SECONDS, 1800)
        self.assertEqual(probe.SOLVE_EXTERNAL_PROCESS_CAP_SECONDS, 1860)
        self.assertEqual(probe.SCIP_PARAMS["limits/time"], 1800)

    def test_external_watchdog_terminates_on_solve_external_cap(self):
        class FakeProcess:
            pid = 12345
            exitcode = None

            def __init__(self):
                self.calls = 0

            def is_alive(self):
                self.calls += 1
                return self.calls == 1

        with tempfile.TemporaryDirectory() as directory:
            scenario_dir = Path(directory)
            probe.write_json(
                probe.phase_state_path(scenario_dir),
                {
                    "phase": "solve",
                    "started_at_epoch": 100.0,
                    "solver_optimization_limit_seconds": 1800,
                    "external_process_cap_seconds": 1860,
                },
            )
            with mock.patch.object(probe, "process_current_rss_bytes", return_value=1), mock.patch.object(
                probe.time, "time", return_value=1961.0
            ), mock.patch.object(probe, "terminate_process_group") as terminate_mock:
                record = probe.monitor_scenario_process(FakeProcess(), scenario_dir)

        self.assertEqual(record["stop_reason"], "solve_external_process_cap_exceeded")
        self.assertEqual(record["solver_optimization_limit_seconds"], 1800)
        self.assertEqual(record["external_process_cap_seconds"], 1860)
        terminate_mock.assert_called_once_with(12345)

    def test_native_scip_statistics_are_captured_at_solve_seam(self):
        class FakeModel:
            def getStatus(self):
                return "timelimit"

            def getSolvingTime(self):
                return 1800.1

            def getPrimalbound(self):
                return 10.0

            def getDualbound(self):
                return 8.0

            def getGap(self):
                return 0.2

            def getNSols(self):
                return 1

            def getNNodes(self):
                return 42

            def getBestSol(self):
                return object()

            def getObjVal(self):
                return 10.0

        class FakeSCIP:
            def _solve(self, model, variables, constraints, data, dims):
                return {"status": "ordinary-result"}

        scip_module = types.ModuleType("cvxpy.reductions.solvers.conic_solvers.scip_conif")
        scip_module.SCIP = FakeSCIP
        package_names = [
            "cvxpy",
            "cvxpy.reductions",
            "cvxpy.reductions.solvers",
            "cvxpy.reductions.solvers.conic_solvers",
        ]
        fake_modules = {name: types.ModuleType(name) for name in package_names}
        for module in fake_modules.values():
            module.__path__ = []
        fake_modules["cvxpy.reductions.solvers.conic_solvers.scip_conif"] = scip_module

        stats = {}
        with mock.patch.dict(sys.modules, fake_modules):
            original = FakeSCIP._solve
            with probe.instrument_native_scip_statistics(stats):
                result = FakeSCIP()._solve(FakeModel(), [], [], {}, {})
            self.assertIs(FakeSCIP._solve, original)

        self.assertEqual(result, {"status": "ordinary-result"})
        self.assertEqual(stats["status"], "timelimit")
        self.assertEqual(stats["solving_time_seconds"], 1800.1)
        self.assertEqual(stats["primal_bound"], 10.0)
        self.assertEqual(stats["dual_bound"], 8.0)
        self.assertEqual(stats["gap"], 0.2)
        self.assertEqual(stats["solution_count"], 1)
        self.assertEqual(stats["node_count"], 42)
        self.assertTrue(stats["has_best_solution"])
        self.assertEqual(stats["objective_value"], 10.0)

    def test_native_scip_statistics_represent_unavailable_fields_as_null(self):
        class PartialModel:
            def getStatus(self):
                return "infeasible"

            def getSolvingTime(self):
                return 0.5

            def getBestSol(self):
                return None

            def getGap(self):
                raise RuntimeError("not available")

        stats = probe.capture_native_scip_statistics(PartialModel())

        self.assertEqual(stats["status"], "infeasible")
        self.assertEqual(stats["solving_time_seconds"], 0.5)
        self.assertIsNone(stats["primal_bound"])
        self.assertIsNone(stats["dual_bound"])
        self.assertIsNone(stats["gap"])
        self.assertIsNone(stats["solution_count"])
        self.assertIsNone(stats["node_count"])
        self.assertFalse(stats["has_best_solution"])
        self.assertIsNone(stats["objective_value"])

    def test_instrumented_and_ordinary_tiny_solve_match_when_scip_available(self):
        try:
            import cvxpy
        except ModuleNotFoundError as exc:
            self.skipTest(f"dependency unavailable: {exc}")
        if "SCIP" not in cvxpy.installed_solvers():
            self.skipTest("SCIP solver unavailable")

        fixture = probe.deterministic_fixture(2)
        ordinary_problem, _, _ = probe.build_pinned_solve_c1_problem(
            fixture.clusters,
            fixture.weights,
            fixture.s_matrix,
            fixture.similarities,
            None,
            probe.DELTA,
            probe.EPSILON,
            probe.STAGE_A_SPLITS,
            expected_endpoint_counts=fixture.endpoint_counts,
            expected_classes=fixture.classes,
        )
        instrumented_problem, _, _ = probe.build_pinned_solve_c1_problem(
            fixture.clusters,
            fixture.weights,
            fixture.s_matrix,
            fixture.similarities,
            None,
            probe.DELTA,
            probe.EPSILON,
            probe.STAGE_A_SPLITS,
            expected_endpoint_counts=fixture.endpoint_counts,
            expected_classes=fixture.classes,
        )
        tiny_params = dict(probe.SCIP_PARAMS)
        tiny_params["limits/time"] = 30

        ordinary_value = ordinary_problem.solve(solver=cvxpy.SCIP, qcp=True, verbose=False, scip_params=tiny_params)
        native_stats = {}
        with probe.instrument_native_scip_statistics(native_stats):
            instrumented_value = instrumented_problem.solve(solver=cvxpy.SCIP, qcp=True, verbose=False, scip_params=tiny_params)

        self.assertEqual(instrumented_problem.status, ordinary_problem.status)
        self.assertAlmostEqual(instrumented_value, ordinary_value, places=7)
        self.assertTrue(native_stats)

    def test_solver_statistics_collects_only_exposed_fields(self):
        solver_stats = types.SimpleNamespace(
            solve_time=12.5,
            setup_time=None,
            extra_stats={
                "status": "timelimit",
                "primal_bound": 10.0,
                "dual_bound": 8.0,
                "gap": 0.2,
                "solution_count": 1,
                "node_count": 42,
            },
        )
        problem = types.SimpleNamespace(status="user_limit", solver_stats=solver_stats)

        stats = probe.collect_solver_statistics(problem)

        self.assertEqual(stats["cvxpy_status"], "user_limit")
        self.assertEqual(stats["status"], "timelimit")
        self.assertEqual(stats["solving_time_seconds"], 12.5)
        self.assertEqual(stats["primal_bound"], 10.0)
        self.assertEqual(stats["dual_bound"], 8.0)
        self.assertEqual(stats["gap"], 0.2)
        self.assertEqual(stats["solution_count"], 1)
        self.assertEqual(stats["node_count"], 42)

        unavailable = probe.collect_solver_statistics(types.SimpleNamespace(status="optimal", solver_stats=types.SimpleNamespace(extra_stats={})))
        self.assertNotIn("primal_bound", unavailable)
        self.assertNotIn("node_count", unavailable)

    def test_output_protection(self):
        with tempfile.TemporaryDirectory() as directory:
            out = Path(directory)
            (out / "existing.txt").write_text("keep\n")
            with self.assertRaises(FileExistsError):
                probe.ensure_empty_output_dir(out)

    def test_stage_b_excluded_from_default_ladder(self):
        self.assertNotIn(probe.STAGE_B_SCENARIO, probe.default_scenarios())
        with self.assertRaises(ValueError):
            probe.default_scenarios(include_stage_b=True)

    def test_only_p0_is_authorized_and_defaulted(self):
        args = probe.parse_args(["--output-dir", "out"])
        self.assertEqual(args.scenarios, [100])
        probe.validate_authorized_scenarios([100])
        with self.assertRaises(ValueError):
            probe.validate_authorized_scenarios([100, 500])
        with self.assertRaises(ValueError):
            probe.validate_authorized_scenarios([probe.STAGE_B_SCENARIO])

    def test_runtime_guard_checks_python_and_pinned_packages(self):
        fake_cvxpy = types.SimpleNamespace(__version__=probe.CVXPY_VERSION, installed_solvers=lambda: ["SCIP"])
        with mock.patch.dict(sys.modules, {"cvxpy": fake_cvxpy}), mock.patch.object(
            probe.importlib.metadata, "version", return_value=probe.PYSCIPOPT_VERSION
        ), mock.patch.object(probe, "observed_scip_version", return_value="9.1.0"), mock.patch.object(
            probe.sys, "version_info", types.SimpleNamespace(major=3, minor=12)
        ):
            probe.validate_runtime_dependencies()

        with mock.patch.dict(sys.modules, {"cvxpy": fake_cvxpy}), mock.patch.object(
            probe.importlib.metadata, "version", return_value=probe.PYSCIPOPT_VERSION
        ), mock.patch.object(probe, "observed_scip_version", return_value="9.2.0"), mock.patch.object(
            probe.sys, "version_info", types.SimpleNamespace(major=3, minor=12)
        ):
            with self.assertRaises(RuntimeError):
                probe.validate_runtime_dependencies()

    def test_probe_does_not_reference_real_admet_data_or_molecular_files(self):
        text = Path(probe.__file__).read_text()
        forbidden = ("admet/data", ".sdf", ".smi", "fingerprint", "DataWarrior")
        for token in forbidden:
            with self.subTest(token=token):
                self.assertNotIn(token, text)

    def test_metadata_and_hash_artifacts_are_json_recoverable(self):
        with tempfile.TemporaryDirectory() as directory:
            out = Path(directory)
            probe.ensure_empty_output_dir(out)
            probe.write_json(out / "metadata.json", {"scenario": 100})
            probe.write_json(out / "results.json", [{"status": "completed"}])
            probe.write_hash_manifest(out)

            self.assertEqual(json.loads((out / "metadata.json").read_text())["scenario"], 100)
            self.assertIn("metadata.json", (out / "SHA256SUMS").read_text())


if __name__ == "__main__":
    unittest.main()
