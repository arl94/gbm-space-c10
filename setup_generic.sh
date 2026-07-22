#!/bin/bash
# =============================================================================
# C10 — setup, for any machine (laptop, or any HPC cluster).
#
#   git clone https://github.com/arl94/gbm-space-c10.git
#   cd gbm-space-c10
#   bash setup_generic.sh                 # CPU environment (the usual choice)
#   bash setup_generic.sh --gpu           # CUDA environment, Linux x86-64 only
#
# What it does:
#   1. finds conda wherever it lives and enables it for future shells
#   2. creates the C10 environment from environment-cpu.yml (or -gpu.yml)
#   3. verifies every package the notebooks import
#   4. registers a Jupyter kernel so VS Code and Jupyter can see the environment
#   5. tells you how to fetch the datasets
#
# `setup.sh` (no suffix) is the original IFB-course version, kept for reference:
# it assumes the shared instructor environment and hard-fails anywhere else.
#
# NOTE: this only sets things up. On a cluster, run heavy compute through the
#       scheduler, never on the login node.
# =============================================================================
set -o pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
FLAVOR="cpu"
[ "${1:-}" = "--gpu" ] && FLAVOR="gpu"
SPEC="$REPO_DIR/environment-${FLAVOR}.yml"
ENV_NAME="c10"
[ "$FLAVOR" = "gpu" ] && ENV_NAME="c10-gpu"

echo "==============================================================="
echo " C10 setup   (repo: $REPO_DIR, environment: $ENV_NAME)"
echo "==============================================================="

# --- 1. find conda ------------------------------------------------------------
echo
echo "[1/5] Locating conda"
CONDA_SH=""
if [ -n "${CONDA_EXE:-}" ] && [ -f "$(dirname "$(dirname "$CONDA_EXE")")/etc/profile.d/conda.sh" ]; then
  CONDA_SH="$(dirname "$(dirname "$CONDA_EXE")")/etc/profile.d/conda.sh"
else
  for base in "$HOME/miniforge3" "$HOME/miniconda3" "$HOME/anaconda3" \
              /opt/conda /usr/local/miniconda3 /shared/software/miniconda; do
    [ -f "$base/etc/profile.d/conda.sh" ] && { CONDA_SH="$base/etc/profile.d/conda.sh"; break; }
  done
fi
# On many clusters conda only appears after `module load`.
if [ -z "$CONDA_SH" ] && command -v module >/dev/null 2>&1; then
  module load conda 2>/dev/null || module load Anaconda3 2>/dev/null || true
  [ -n "${CONDA_EXE:-}" ] && CONDA_SH="$(dirname "$(dirname "$CONDA_EXE")")/etc/profile.d/conda.sh"
fi
if [ -z "$CONDA_SH" ] || [ ! -f "$CONDA_SH" ]; then
  echo "      ERROR: no conda found." >&2
  echo "      Install Miniforge: https://conda-forge.org/download/" >&2
  echo "      Or set CONDA_EXE to your conda binary and re-run." >&2
  exit 1
fi
echo "      found: $CONDA_SH"
source "$CONDA_SH"
conda init bash >/dev/null 2>&1 || true
conda config --set auto_activate_base false 2>/dev/null || true

# --- 2. create the environment ------------------------------------------------
echo
echo "[2/5] Creating the '$ENV_NAME' environment from $(basename "$SPEC")"
if [ ! -f "$SPEC" ]; then
  echo "      ERROR: $SPEC not found." >&2
  exit 1
fi
if conda env list | awk '{print $1}' | grep -qx "$ENV_NAME"; then
  echo "      '$ENV_NAME' already exists — leaving it alone."
  echo "      To rebuild:  conda env remove -n $ENV_NAME && bash $(basename "$0") ${1:-}"
else
  # mamba is much faster when available.
  if command -v mamba >/dev/null 2>&1; then
    mamba env create -f "$SPEC" || exit 1
  else
    conda env create -f "$SPEC" || exit 1
  fi
fi

# --- 3. verify ----------------------------------------------------------------
echo
echo "[3/5] Verifying the environment"
conda activate "$ENV_NAME" || { echo "      ERROR: could not activate $ENV_NAME" >&2; exit 1; }
python - <<'PY' || exit 1
import importlib.util, sys
mods = ["scanpy", "anndata", "scvi", "cell2location", "celltypist", "infercnvpy",
        "squidpy", "harmonypy", "liana", "decoupler", "pyarrow", "torch"]
missing = [m for m in mods if importlib.util.find_spec(m) is None]
if missing:
    print("      MISSING packages:", missing)
    sys.exit(1)
print(f"      env OK -- python {sys.version.split()[0]}, all {len(mods)} key packages import.")
PY
if [ "$FLAVOR" = "gpu" ]; then
  python -c "import torch; print('      torch.cuda.is_available() =', torch.cuda.is_available())"
fi

# --- 4. Jupyter kernel --------------------------------------------------------
echo
echo "[4/5] Registering the Jupyter kernel"
python -m ipykernel install --user --name "$ENV_NAME" \
       --display-name "Python ($ENV_NAME)" >/dev/null 2>&1 \
  && echo "      kernel registered." \
  || echo "      (kernel registration skipped -- not fatal; pick the env in VS Code instead)"

# --- 5. data ------------------------------------------------------------------
echo
echo "[5/5] Datasets"
if python "$REPO_DIR/scripts/check_c10_data.py" >/dev/null 2>&1; then
  echo "      all datasets already present."
else
  echo "      not fetched yet. See data/README.md, then run:"
  echo "        bash scripts/fetch_c10_data.sh <bundle-location>"
  echo "        python scripts/check_c10_data.py"
fi

echo
echo "==============================================================="
echo " Setup complete."
echo "   * Activate anytime:  conda activate $ENV_NAME"
echo "   * Start working:     jupyter lab notebooks/level1"
echo "   * Paths resolve themselves -- nothing to edit. See README.md."
echo "   * Level 1 on the full dataset peaks at ~23 GB RSS. On a 16 GB"
echo "     machine, subsample first (see docs/local_install_mac_windows.md)."
echo "==============================================================="
