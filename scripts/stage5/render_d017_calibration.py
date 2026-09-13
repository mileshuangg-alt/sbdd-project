#!/usr/bin/env python3
"""Render D017 review artifacts from an existing US-align superposition."""

from __future__ import annotations

import argparse
from pathlib import Path

from evaluation.d017_visualization import render_whole_structure


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--superposition-cif", type=Path, required=True)
    parser.add_argument("--reference-cif", type=Path, required=True)
    parser.add_argument("--superposition-chain", required=True)
    parser.add_argument("--reference-chain", required=True)
    parser.add_argument("--output-png", type=Path, required=True)
    parser.add_argument("--output-pml", type=Path, required=True)
    args = parser.parse_args()

    render_whole_structure(
        superposition_cif=args.superposition_cif,
        reference_cif=args.reference_cif,
        superposition_chain=args.superposition_chain,
        reference_chain=args.reference_chain,
        output_png=args.output_png,
        output_pml=args.output_pml,
    )


if __name__ == "__main__":
    main()
