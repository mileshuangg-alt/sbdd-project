"""Streaming production build for the Stage-6 planner-stock contract.

This module wires together the already-tested scientific primitives from
stage6_planner_stock_contract.py. It does not introduce new planner identity
semantics.

The production runner:
  * streams the frozen D026/D027 identity TSV;
  * validates every source row;
  * canonicalizes every source row for ASKCOS;
  * requires repeated D026 identities to have consistent ASKCOS outcomes;
  * builds the exact AiZynthFinder full-key stock;
  * builds the ASKCOS representation/accounting artifacts;
  * excludes canonical-collision groups under D028 Amendment 1;
  * exempts ASKCOS representation failures under D028 Amendment 2;
  * performs a complete streaming set-equality proof across representable keys.
"""

from __future__ import annotations

import csv
import hashlib
import json
import os
import signal
import shutil
import sqlite3
import time
import traceback
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Iterable

from evaluation.stage6_planner_stock_contract import (
    ASKCOS_STATUS_CANONICAL_COLLISION_EXCLUDED,
    ASKCOS_STATUS_REPRESENTATION_FAILURE,
    canonicalize_askcos_smiles,
    read_frozen_identity_record,
)


EXPECTED_SOURCE_FIELDS = (
    "smiles",
    "zinc_id",
    "zinc_inchikey",
    "d026_inchikey",
    "full_key_match",
    "connectivity_match",
    "source_file",
    "source_line_number",
)


def iter_frozen_d026_records(
    source_path: str | Path,
) -> Iterable[dict[str, str]]:
    """Stream validated frozen D026/D027 source rows."""

    source_path = Path(source_path)

    with source_path.open(
        "r",
        encoding="utf-8",
        newline="",
    ) as handle:
        reader = csv.DictReader(handle, delimiter="\t")

        if tuple(reader.fieldnames or ()) != EXPECTED_SOURCE_FIELDS:
            raise ValueError(
                "unexpected frozen D026 source header"
            )

        for row in reader:
            yield row


def _hash_sorted_keys(keys: Iterable[str]) -> str:
    """Hash sorted unique keys with the frozen newline serialization."""

    digest = hashlib.sha256()

    previous = None

    for key in keys:
        if not isinstance(key, str) or key == "":
            raise ValueError("cannot hash an empty molecular identity")

        if previous == key:
            raise ValueError(
                f"duplicate key in sorted identity stream: {key}"
            )

        digest.update(key.encode("utf-8"))
        digest.update(b"\n")
        previous = key

    return digest.hexdigest()


def hash_sorted_key_file(
    path: str | Path,
) -> tuple[int, str]:
    """Hash one sorted, one-key-per-line identity artifact exactly."""

    path = Path(path)

    def lines():
        with path.open(
            "r",
            encoding="utf-8",
            newline="",
        ) as handle:
            previous = None

            for raw_line in handle:
                key = raw_line.rstrip("\n")

                if key == "":
                    raise ValueError(
                        f"empty identity encountered in {path}"
                    )

                if previous is not None and key <= previous:
                    raise ValueError(
                        f"identity file is not strictly sorted: {path}"
                    )

                previous = key
                yield key

    count = 0
    digest = hashlib.sha256()

    for key in lines():
        digest.update(key.encode("utf-8"))
        digest.update(b"\n")
        count += 1

    return count, digest.hexdigest()


def compare_sorted_key_files(
    left_path: str | Path,
    right_path: str | Path,
    left_only_path: str | Path,
    right_only_path: str | Path,
) -> dict[str, int | bool]:
    """Perform complete streaming set comparison of two sorted key files."""

    def iterator(path: str | Path):
        with Path(path).open(
            "r",
            encoding="utf-8",
            newline="",
        ) as handle:
            for raw_line in handle:
                yield raw_line.rstrip("\n")

    left = iterator(left_path)
    right = iterator(right_path)

    left_key = next(left, None)
    right_key = next(right, None)

    left_only_count = 0
    right_only_count = 0

    with (
        Path(left_only_path).open(
            "w",
            encoding="utf-8",
            newline="\n",
        ) as left_only,
        Path(right_only_path).open(
            "w",
            encoding="utf-8",
            newline="\n",
        ) as right_only,
    ):
        while left_key is not None or right_key is not None:
            if right_key is None or (
                left_key is not None and left_key < right_key
            ):
                left_only.write(left_key + "\n")
                left_only_count += 1
                left_key = next(left, None)
                continue

            if left_key is None or right_key < left_key:
                right_only.write(right_key + "\n")
                right_only_count += 1
                right_key = next(right, None)
                continue

            left_key = next(left, None)
            right_key = next(right, None)

    result = {
        "left_only_count": left_only_count,
        "right_only_count": right_only_count,
        "set_equality_pass": (
            left_only_count == 0
            and right_only_count == 0
        ),
    }
    return result


def _make_local_workspace(local_work_dir: Path) -> Path:
    """Create one run-specific local workspace below the configured root."""

    local_work_dir.mkdir(parents=True, exist_ok=True)

    workspace = (
        local_work_dir
        / f"stage6_planner_stock_build_{uuid.uuid4().hex}"
    )
    workspace.mkdir()
    return workspace


def _copy_artifacts_atomically(
    artifact_paths: Iterable[Path],
    output_dir: Path,
) -> None:
    """Publish finalized artifacts with per-file temp copies and renames."""

    output_dir.mkdir(parents=True, exist_ok=True)

    copy_token = uuid.uuid4().hex

    paths = list(artifact_paths)
    ordered_paths = [
        path for path in paths if path.name not in {"proof.json", "manifest.json"}
    ]
    ordered_paths.extend(
        path for name in ("proof.json", "manifest.json")
        for path in paths
        if path.name == name
    )

    for source_path in ordered_paths:
        destination_path = output_dir / source_path.name
        temporary_path = output_dir / (
            f".{source_path.name}.tmp.{copy_token}"
        )

        try:
            shutil.copy2(source_path, temporary_path)
            os.replace(temporary_path, destination_path)
        finally:
            if temporary_path.exists():
                temporary_path.unlink()


def _progress_timestamp() -> str:
    return datetime.now(UTC).isoformat()


def run_stage6_planner_stock_build(
    source_path: str | Path,
    output_dir: str | Path,
    expected_source_records: int | None = None,
    local_work_dir: str | Path | None = None,
    _progress_interval_records: int = 100000,
) -> dict[str, object]:
    """Execute the complete streaming planner-stock construction."""

    if local_work_dir is None:
        raise ValueError(
            "local_work_dir is required; SQLite and intermediate artifacts "
            "must be built on local scratch, not in the final output directory"
        )

    if _progress_interval_records <= 0:
        raise ValueError("progress interval must be positive")

    source_path = Path(source_path).expanduser().resolve()
    output_dir = Path(output_dir).expanduser().resolve()
    local_work_dir = Path(local_work_dir).expanduser().resolve()
    local_workspace = _make_local_workspace(local_work_dir)

    database_path = local_workspace / "planner_stock_build.sqlite"
    progress_log_path = local_workspace / "progress.log"

    start_time = time.monotonic()
    total_source_records = 0
    connection = None

    progress_log = progress_log_path.open(
        "a",
        encoding="utf-8",
        newline="\n",
    )

    def log_progress(message: str) -> None:
        elapsed_seconds = time.monotonic() - start_time
        progress_log.write(
            f"{_progress_timestamp()}\t"
            f"elapsed_seconds={elapsed_seconds:.3f}\t"
            f"{message}\n"
        )
        progress_log.flush()

    def handle_termination_signal(signum, frame):
        signal_name = signal.Signals(signum).name
        log_progress(
            "signal_received "
            f"signal={signal_name} signum={signum} "
            f"source_rows_processed={total_source_records}"
        )
        raise SystemExit(128 + signum)

    previous_signal_handlers = {}

    for signal_number in (signal.SIGTERM, signal.SIGINT):
        previous_signal_handlers[signal_number] = signal.getsignal(
            signal_number
        )
        signal.signal(signal_number, handle_termination_signal)

    try:
        log_progress(
            "run_started "
            f"source_path={source_path} "
            f"local_workspace={local_workspace} "
            f"final_output_dir={output_dir}"
        )

        connection = sqlite3.connect(database_path)

        connection.execute(
            """
            CREATE TABLE source_identities (
                d026_inchikey TEXT PRIMARY KEY,
                source_smiles TEXT NOT NULL,
                source_row_count INTEGER NOT NULL,
                askcos_status TEXT,
                canonical_smiles TEXT,
                failure_reason TEXT
            )
            """
        )

        connection.execute(
            """
            CREATE TABLE askcos_canonical_identity (
                canonical_smiles TEXT NOT NULL,
                d026_inchikey TEXT NOT NULL,
                PRIMARY KEY (canonical_smiles, d026_inchikey)
            )
            """
        )

        connection.execute(
            """
            CREATE INDEX idx_askcos_canonical
            ON askcos_canonical_identity(canonical_smiles)
            """
        )

        total_source_records = 0
        source_duplicate_rows = 0
        identity_representation_conflicts = 0

        conflict_path = (
            local_workspace
            / "source_identity_representation_conflicts.tsv"
        )

        with conflict_path.open(
            "w",
            encoding="utf-8",
            newline="\n",
        ) as conflict_handle:
            conflict_handle.write(
                "d026_inchikey\t"
                "existing_status\t"
                "existing_canonical_smiles\t"
                "existing_failure_reason\t"
                "new_status\t"
                "new_canonical_smiles\t"
                "new_failure_reason\n"
            )

            for row in iter_frozen_d026_records(source_path):
                total_source_records += 1

                source_record = read_frozen_identity_record(row)
                d026_inchikey = source_record["d026_inchikey"]

                representation = canonicalize_askcos_smiles(
                    source_record
                )

                status = representation["askcos_status"]
                canonical_smiles = representation["canonical_smiles"]
                failure_reason = (
                    representation["representation_failure_reason"]
                )

                existing = connection.execute(
                    """
                    SELECT
                        source_row_count,
                        askcos_status,
                        canonical_smiles,
                        failure_reason
                    FROM source_identities
                    WHERE d026_inchikey = ?
                    """,
                    (d026_inchikey,),
                ).fetchone()

                if existing is None:
                    connection.execute(
                        """
                        INSERT INTO source_identities (
                            d026_inchikey,
                            source_smiles,
                            source_row_count,
                            askcos_status,
                            canonical_smiles,
                            failure_reason
                        )
                        VALUES (?, ?, 1, ?, ?, ?)
                        """,
                        (
                            d026_inchikey,
                            source_record["smiles"],
                            status,
                            canonical_smiles,
                            failure_reason,
                        ),
                    )
                else:
                    (
                        source_row_count,
                        old_status,
                        old_canonical_smiles,
                        old_failure_reason,
                    ) = existing

                    source_duplicate_rows += 1

                    if (
                        old_status != status
                        or old_canonical_smiles != canonical_smiles
                        or old_failure_reason != failure_reason
                    ):
                        identity_representation_conflicts += 1

                        conflict_handle.write(
                            f"{d026_inchikey}\t"
                            f"{old_status}\t"
                            f"{old_canonical_smiles or ''}\t"
                            f"{old_failure_reason or ''}\t"
                            f"{status}\t"
                            f"{canonical_smiles or ''}\t"
                            f"{failure_reason or ''}\n"
                        )

                    connection.execute(
                        """
                        UPDATE source_identities
                        SET source_row_count = ?
                        WHERE d026_inchikey = ?
                        """,
                        (
                            source_row_count + 1,
                            d026_inchikey,
                        ),
                    )

                if status == "representable":
                    connection.execute(
                        """
                        INSERT OR IGNORE INTO askcos_canonical_identity (
                            canonical_smiles,
                            d026_inchikey
                        )
                        VALUES (?, ?)
                        """,
                        (
                            canonical_smiles,
                            d026_inchikey,
                        ),
                    )

                if total_source_records % _progress_interval_records == 0:
                    connection.commit()
                    log_progress(
                        "source_progress "
                        f"source_rows_processed={total_source_records}"
                    )

        connection.commit()

        if (
            expected_source_records is not None
            and total_source_records != expected_source_records
        ):
            raise RuntimeError(
                "frozen source record count mismatch: "
                f"observed={total_source_records}, "
                f"expected={expected_source_records}"
            )

        if identity_representation_conflicts:
            raise RuntimeError(
                "one or more duplicated D026 identities produced "
                "inconsistent ASKCOS representations; see "
                "source_identity_representation_conflicts.tsv"
            )

        unique_frozen_keys = connection.execute(
            """
            SELECT COUNT(*)
            FROM source_identities
            """
        ).fetchone()[0]

        representation_failure_keys = connection.execute(
            """
            SELECT COUNT(*)
            FROM source_identities
            WHERE askcos_status = ?
            """,
            (ASKCOS_STATUS_REPRESENTATION_FAILURE,),
        ).fetchone()[0]

        collision_canonical_count = connection.execute(
            """
            SELECT COUNT(*)
            FROM (
                SELECT canonical_smiles
                FROM askcos_canonical_identity
                GROUP BY canonical_smiles
                HAVING COUNT(DISTINCT d026_inchikey) > 1
            )
            """
        ).fetchone()[0]

        collision_key_count = connection.execute(
            """
            SELECT COUNT(DISTINCT d026_inchikey)
            FROM askcos_canonical_identity
            WHERE canonical_smiles IN (
                SELECT canonical_smiles
                FROM askcos_canonical_identity
                GROUP BY canonical_smiles
                HAVING COUNT(DISTINCT d026_inchikey) > 1
            )
            """
        ).fetchone()[0]

        qualified_key_count = connection.execute(
            """
            SELECT COUNT(*)
            FROM askcos_canonical_identity AS a
            WHERE a.canonical_smiles NOT IN (
                SELECT canonical_smiles
                FROM askcos_canonical_identity
                GROUP BY canonical_smiles
                HAVING COUNT(DISTINCT d026_inchikey) > 1
            )
            """
        ).fetchone()[0]

        representable_key_count = connection.execute(
            """
            SELECT COUNT(*)
            FROM source_identities
            WHERE askcos_status = 'representable'
            """
        ).fetchone()[0]

        if (
            representation_failure_keys
            + representable_key_count
            != unique_frozen_keys
        ):
            raise AssertionError(
                "frozen identity / ASKCOS representability accounting "
                "does not reconcile"
            )

        aizynth_path = local_workspace / "aizynthfinder_d026_stock.txt"
        aizynth_representable_path = (
            local_workspace / "aizynthfinder_representable_d026_keys.txt"
        )
        representable_path = (
            local_workspace
            / "askcos_representable_d026_keys.txt"
        )
        accounting_path = (
            local_workspace
            / "askcos_identity_accounting.tsv"
        )
        failure_path = (
            local_workspace
            / "askcos_representation_failures.tsv"
        )
        collision_path = (
            local_workspace
            / "askcos_collision_exclusions.tsv"
        )
        qualified_path = (
            local_workspace
            / "askcos_qualified_stock.tsv"
        )

        with aizynth_path.open(
            "w",
            encoding="utf-8",
            newline="\n",
        ) as handle:
            for (d026_inchikey,) in connection.execute(
                """
                SELECT d026_inchikey
                FROM source_identities
                ORDER BY d026_inchikey ASC
                """
            ):
                handle.write(d026_inchikey + "\n")

        with representable_path.open(
            "w",
            encoding="utf-8",
            newline="\n",
        ) as handle:
            for (d026_inchikey,) in connection.execute(
                """
                SELECT d026_inchikey
                FROM source_identities
                WHERE askcos_status = 'representable'
                ORDER BY d026_inchikey ASC
                """
            ):
                handle.write(d026_inchikey + "\n")

        # D028 Amendment 2: representation failures are exempt from the
        # equality proof. Restrict the AiZynthFinder identity set to the
        # same ASKCOS-representable frozen domain before comparison.
        with aizynth_representable_path.open(
            "w",
            encoding="utf-8",
            newline="\n",
        ) as handle:
            for (d026_inchikey,) in connection.execute(
                """
                SELECT d026_inchikey
                FROM source_identities
                WHERE askcos_status = 'representable'
                ORDER BY d026_inchikey ASC
                """
            ):
                handle.write(d026_inchikey + "\n")

        with accounting_path.open(
            "w",
            encoding="utf-8",
            newline="\n",
        ) as handle:
            handle.write(
                "d026_inchikey\t"
                "askcos_status\t"
                "canonical_smiles\t"
                "representation_failure_reason\n"
            )

            rows = connection.execute(
                """
                SELECT
                    d026_inchikey,
                    askcos_status,
                    canonical_smiles,
                    failure_reason
                FROM source_identities
                ORDER BY d026_inchikey ASC
                """
            )

            for (
                d026_inchikey,
                status,
                canonical_smiles,
                failure_reason,
            ) in rows:
                handle.write(
                    f"{d026_inchikey}\t"
                    f"{status}\t"
                    f"{canonical_smiles or ''}\t"
                    f"{failure_reason or ''}\n"
                )

        with failure_path.open(
            "w",
            encoding="utf-8",
            newline="\n",
        ) as handle:
            handle.write(
                "d026_inchikey\trepresentation_failure_reason\n"
            )

            rows = connection.execute(
                """
                SELECT
                    d026_inchikey,
                    failure_reason
                FROM source_identities
                WHERE askcos_status = ?
                ORDER BY d026_inchikey ASC
                """,
                (ASKCOS_STATUS_REPRESENTATION_FAILURE,),
            )

            for d026_inchikey, failure_reason in rows:
                handle.write(
                    f"{d026_inchikey}\t{failure_reason}\n"
                )

        with collision_path.open(
            "w",
            encoding="utf-8",
            newline="\n",
        ) as handle:
            handle.write(
                "canonical_smiles\td026_inchikey\n"
            )

            rows = connection.execute(
                """
                SELECT
                    canonical_smiles,
                    d026_inchikey
                FROM askcos_canonical_identity
                WHERE canonical_smiles IN (
                    SELECT canonical_smiles
                    FROM askcos_canonical_identity
                    GROUP BY canonical_smiles
                    HAVING COUNT(DISTINCT d026_inchikey) > 1
                )
                ORDER BY canonical_smiles ASC, d026_inchikey ASC
                """
            )

            for canonical_smiles, d026_inchikey in rows:
                handle.write(
                    f"{canonical_smiles}\t{d026_inchikey}\n"
                )

        with qualified_path.open(
            "w",
            encoding="utf-8",
            newline="\n",
        ) as handle:
            handle.write(
                "d026_inchikey\tcanonical_smiles\n"
            )

            rows = connection.execute(
                """
                SELECT
                    d026_inchikey,
                    canonical_smiles
                FROM askcos_canonical_identity
                WHERE canonical_smiles NOT IN (
                    SELECT canonical_smiles
                    FROM askcos_canonical_identity
                    GROUP BY canonical_smiles
                    HAVING COUNT(DISTINCT d026_inchikey) > 1
                )
                ORDER BY d026_inchikey ASC
                """
            )

            for d026_inchikey, canonical_smiles in rows:
                handle.write(
                    f"{d026_inchikey}\t{canonical_smiles}\n"
                )

        aizynth_count, aizynth_sha256 = hash_sorted_key_file(
            aizynth_path
        )
        representable_count, representable_sha256 = (
            hash_sorted_key_file(representable_path)
        )
        aizynth_representable_count, aizynth_representable_sha256 = (
            hash_sorted_key_file(aizynth_representable_path)
        )

        left_only_path = (
            local_workspace / "set_difference_representable_only.txt"
        )
        right_only_path = (
            local_workspace
            / "set_difference_aizynthfinder_representable_only.txt"
        )

        proof = compare_sorted_key_files(
            representable_path,
            aizynth_representable_path,
            left_only_path,
            right_only_path,
        )

        if representable_count != representable_key_count:
            raise AssertionError(
                "ASKCOS representable artifact count does not reconcile "
                "with database"
            )

        if aizynth_representable_count != representable_key_count:
            raise AssertionError(
                "AiZynthFinder representable-domain artifact count does "
                "not reconcile with database"
            )

        if (
            aizynth_representable_count + representation_failure_keys
            != aizynth_count
        ):
            raise AssertionError(
                "full AiZynthFinder stock does not reconcile with the "
                "ASKCOS representability partition"
            )

        if not proof["set_equality_pass"]:
            raise AssertionError(
                "representable D026 identity set equality proof failed"
            )

        proof_result = {
            "authorized_claim": (
                "set equality across all representable keys"
            ),
            "frozen_d026_key_count": unique_frozen_keys,
            "askcos_representation_failure_count": (
                representation_failure_keys
            ),
            "askcos_collision_excluded_count": collision_key_count,
            "askcos_qualified_count": qualified_key_count,
            "askcos_representable_count": representable_key_count,
            "aizynthfinder_count": aizynth_count,
            "aizynthfinder_representable_count": (
                aizynth_representable_count
            ),
            "aizynthfinder_set_sha256": aizynth_sha256,
            "aizynthfinder_representable_set_sha256": (
                aizynth_representable_sha256
            ),
            "askcos_representable_set_sha256": (
                representable_sha256
            ),
            "representable_set_equality_pass": (
                proof["set_equality_pass"]
            ),
            "representable_only_count": (
                proof["left_only_count"]
            ),
            "aizynthfinder_only_count": (
                proof["right_only_count"]
            ),
        }

        proof_path = local_workspace / "proof.json"
        proof_path.write_text(
            json.dumps(
                proof_result,
                indent=2,
                sort_keys=True,
            )
            + "\n",
            encoding="utf-8",
        )

        manifest = {
            "source_path": str(source_path),
            "local_workspace": str(local_workspace),
            "progress_log": str(progress_log_path),
            "final_output_dir": str(output_dir),
            "source_record_count": total_source_records,
            "unique_frozen_d026_keys": unique_frozen_keys,
            "source_duplicate_rows": source_duplicate_rows,
            "identity_representation_conflicts": (
                identity_representation_conflicts
            ),
            "askcos_representation_failure_keys": (
                representation_failure_keys
            ),
            "askcos_collision_canonical_smiles": (
                collision_canonical_count
            ),
            "askcos_collision_excluded_keys": collision_key_count,
            "askcos_qualified_keys": qualified_key_count,
            "askcos_representable_keys": representable_key_count,
            "aizynthfinder_keys": aizynth_count,
            "askcos_representable_set_sha256": (
                representable_sha256
            ),
            "aizynthfinder_set_sha256": aizynth_sha256,
            "set_equality_pass": proof["set_equality_pass"],
            "artifacts": {
                path.name: hash_sorted_key_file(path)[1]
                if path.name in {
                    "aizynthfinder_d026_stock.txt",
                    "aizynthfinder_representable_d026_keys.txt",
                    "askcos_representable_d026_keys.txt",
                }
                else hashlib.sha256(
                    path.read_bytes()
                ).hexdigest()
                for path in (
                    aizynth_path,
                    aizynth_representable_path,
                    representable_path,
                    accounting_path,
                    failure_path,
                    collision_path,
                    qualified_path,
                    left_only_path,
                    right_only_path,
                    proof_path,
                    conflict_path,
                )
            },
        }

        manifest_path = local_workspace / "manifest.json"
        manifest_path.write_text(
            json.dumps(
                manifest,
                indent=2,
                sort_keys=True,
            )
            + "\n",
            encoding="utf-8",
        )

        final_artifact_paths = (
            aizynth_path,
            aizynth_representable_path,
            representable_path,
            accounting_path,
            failure_path,
            collision_path,
            qualified_path,
            left_only_path,
            right_only_path,
            conflict_path,
            proof_path,
            manifest_path,
        )
        _copy_artifacts_atomically(final_artifact_paths, output_dir)

        log_progress(
            "run_completed "
            f"source_record_count={total_source_records} "
            f"unique_frozen_d026_keys={unique_frozen_keys} "
            f"representation_failure_keys={representation_failure_keys} "
            f"collision_excluded_keys={collision_key_count} "
            f"qualified_keys={qualified_key_count} "
            f"representable_keys={representable_key_count} "
            f"aizynthfinder_keys={aizynth_count} "
            f"representable_set_equality_pass={proof['set_equality_pass']}"
        )

        result = {
            "source_record_count": total_source_records,
            "unique_frozen_d026_keys": unique_frozen_keys,
            "source_duplicate_rows": source_duplicate_rows,
            "representation_failure_keys": representation_failure_keys,
            "collision_excluded_keys": collision_key_count,
            "qualified_keys": qualified_key_count,
            "representable_keys": representable_key_count,
            "aizynthfinder_keys": aizynth_count,
            "representable_set_equality_pass": (
                proof["set_equality_pass"]
            ),
            "output_dir": str(output_dir),
            "local_workspace": str(local_workspace),
        }
        return result

    except BaseException as exc:
        log_progress(
            "run_failed "
            f"exception_type={type(exc).__name__} "
            f"source_rows_processed={total_source_records}"
        )
        progress_log.write(
            "".join(
                traceback.format_exception(
                    type(exc),
                    exc,
                    exc.__traceback__,
                )
            )
        )
        progress_log.flush()
        raise

    finally:
        if connection is not None:
            connection.close()
        for signal_number, previous_handler in previous_signal_handlers.items():
            signal.signal(signal_number, previous_handler)
        progress_log.close()
