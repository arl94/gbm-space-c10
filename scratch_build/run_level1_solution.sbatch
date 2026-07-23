#!/bin/bash
#SBATCH --job-name=c10_l1_solution
#SBATCH --partition=cpu
#SBATCH --cpus-per-task=16
#SBATCH --mem=48G
#SBATCH --time=04:00:00
#SBATCH --output=%x_%j.log

# Re-execute the Level 1 answer key end-to-end on the full 118k-nucleus dataset, so every
# cell carries the output it actually produced. Sized from the IFB validation run
# (118k nuclei, ~18 min wall, ~21 GB peak RSS measured on Curnagl with 16 cores).
# NB: no `set -u`. Some conda envs ship an activate.d hook that dereferences an unset
# LD_LIBRARY_PATH; under `set -u` that aborts the job during `conda activate`.
set -eo pipefail

# Resolve the repo: walk up from wherever sbatch was invoked until src/gbmspace_utils appears.
# Override with C10_ROOT=/path/to/repo if you submit from somewhere else entirely.
REPO="${C10_ROOT:-${SLURM_SUBMIT_DIR:-$PWD}}"
while [ "$REPO" != "/" ] && [ ! -d "$REPO/src/gbmspace_utils" ]; do REPO="$(dirname "$REPO")"; done
[ -d "$REPO/src/gbmspace_utils" ] || { echo "ERROR: repo root not found; set C10_ROOT" >&2; exit 1; }

# Find conda wherever it lives (same logic as setup_generic.sh).
if [ -z "${CONDA_EXE:-}" ]; then
  for base in "$HOME/miniforge3" "$HOME/miniconda3" "$HOME/anaconda3" /opt/conda; do
    [ -f "$base/etc/profile.d/conda.sh" ] && { source "$base/etc/profile.d/conda.sh"; break; }
  done
else
  source "$(dirname "$(dirname "$CONDA_EXE")")/etc/profile.d/conda.sh"
fi
command -v conda >/dev/null || { echo "ERROR: no conda found" >&2; exit 1; }
conda activate "${C10_ENV:-c10}"

export OMP_NUM_THREADS=${SLURM_CPUS_PER_TASK}
export MKL_NUM_THREADS=${SLURM_CPUS_PER_TASK}
export NUMBA_NUM_THREADS=${SLURM_CPUS_PER_TASK}

cd "$REPO/notebooks/level1"   # the project-paths cell walks up from here to find the repo root

echo "host=$(hostname) cpus=${SLURM_CPUS_PER_TASK} python=$(which python)"
python -c "import scanpy, infercnvpy, celltypist; print('scanpy', scanpy.__version__)"

time python "$REPO/scratch_build/direct_execute_nb.py" 01_snrna_analysis_solution.ipynb 3600

echo "=== peak RSS ==="
/usr/bin/time -v true 2>/dev/null || true
