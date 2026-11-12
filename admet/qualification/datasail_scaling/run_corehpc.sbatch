#!/bin/bash
#SBATCH --job-name=datasail-s1-scaling
#SBATCH --partition=cpu
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=16
#SBATCH --mem=256G
#SBATCH --time=01:00:00
#SBATCH --output=datasail_s1_scaling_%j.out
#SBATCH --error=datasail_s1_scaling_%j.err

set -euo pipefail

if [ "$#" -ne 2 ]; then
    echo "usage: sbatch run_corehpc.sbatch IMAGE.sif OUTPUT_DIR" >&2
    exit 2
fi

IMAGE="$1"
OUTPUT_DIR="$2"

apptainer exec \
    --cleanenv \
    --bind "${PWD}:/workspace" \
    "${IMAGE}" \
    python /workspace/admet/qualification/datasail_scaling/probe.py \
        --output-dir "${OUTPUT_DIR}"
