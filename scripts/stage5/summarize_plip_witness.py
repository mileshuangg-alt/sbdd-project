import argparse
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(
        0,
        str(ROOT),
    )

from evaluation.plip_witness import (
    load_plip_witness_config,
    summarize_plip_xml,
    summarize_qualification_panel,
)


def parse_args():
    """Parse command-line arguments for the PLIP witness summarizer."""

    parser = argparse.ArgumentParser(
        description="Summarize configured PLIP XML witness interactions."
    )
    parser.add_argument(
        "--config",
        required=True,
        help="Path to a PLIP witness JSON config.",
    )
    parser.add_argument(
        "--xml",
        help="Path to one PLIP XML report. If omitted, run the configured panel.",
    )
    parser.add_argument(
        "--panel-id",
        help="Optional configured panel case ID for the XML report.",
    )
    parser.add_argument(
        "--base-path",
        default=".",
        help="Base path for configured qualification-panel XML paths.",
    )
    parser.add_argument(
        "--output",
        help="Optional JSON output path. If omitted, write to stdout.",
    )

    return parser.parse_args()


def write_summary(summary, output_path=None):
    """Write a compact JSON summary."""

    payload = json.dumps(
        summary,
        indent=2,
        sort_keys=True,
    )

    if output_path is None:
        print(payload)
        return

    output_path = Path(output_path)
    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )
    output_path.write_text(
        payload + "\n"
    )


def main():
    """Run PLIP XML witness summarization."""

    args = parse_args()
    config = load_plip_witness_config(
        args.config
    )

    if args.xml:
        summary = summarize_plip_xml(
            args.xml,
            config,
            panel_id=args.panel_id,
        )
    else:
        summary = summarize_qualification_panel(
            config,
            base_path=args.base_path,
        )

    write_summary(
        summary,
        output_path=args.output,
    )

    return summary


if __name__ == "__main__":
    main()
