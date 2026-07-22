#!/usr/bin/env bash
#
# start_jupyter_generic.sh — launch a PERSISTENT JupyterLab server inside a Slurm job,
# on ANY Slurm cluster.
#
# `start_jupyter.sh` (no suffix) is the original IFB-course version, kept for reference:
# it hardcodes the IFB login host, account and shared environment. This one detects or
# asks for all of that instead.
#
# Run this ON THE LOGIN NODE. It submits a Slurm job that activates your C10 conda
# environment and starts `jupyter lab` bound to the compute node. Because the server
# lives inside the Slurm job (NOT inside your SSH / VS Code session), it keeps running
# when you close your laptop. Reconnect any time while the job is alive.
#
# Usage:
#   ./start_jupyter_generic.sh [--cpus N] [--mem 64G] [--time HH:MM:SS] [--port 8888]
#                              [--account ACC] [--partition PART] [--dir /path]
#                              [--env NAME_OR_PATH] [--login-host HOST]
#
# Every flag also has an environment-variable equivalent:
#   CPUS=16 MEM=128G TIME=12:00:00 ENV_NAME=c10 ./start_jupyter_generic.sh
#
# Cluster-specific settings you will probably need to give it once:
#   --partition   your CPU partition        (else Slurm's default is used)
#   --account     only if your site requires one
#   --login-host  the hostname you SSH to   (auto-detected, override if wrong)
#
# Memory: Level 1 on the full 118k-nucleus dataset peaks at ~23 GB RSS, so --mem 32G
# is a sensible floor and the 64G default is comfortable.
#
# After it prints "Submitted", wait ~10-60 s, then read:  cat ~/jupyter_connect.txt
# ---------------------------------------------------------------------------

set -eo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# ------------------------- defaults (override via env or flags) -------------
ACCOUNT="${ACCOUNT:-}"                       # empty = do not pass --account
PARTITION="${PARTITION:-}"                   # empty = cluster default partition
CPUS="${CPUS:-8}"
MEM="${MEM:-64G}"
TIME="${TIME:-08:00:00}"
PORT="${PORT:-8888}"
NOTEBOOK_DIR="${NOTEBOOK_DIR:-$REPO_DIR}"
ENV_NAME="${ENV_NAME:-c10}"                  # name or full path of the conda env
LOGIN_HOST="${LOGIN_HOST:-$(hostname -f 2>/dev/null || hostname)}"

LOG_DIR="${LOG_DIR:-$HOME/jupyter_logs}"
CONNECT_FILE="${CONNECT_FILE:-$HOME/jupyter_connect.txt}"

# ------------------------------- flag parsing -------------------------------
while [[ $# -gt 0 ]]; do
  case "$1" in
    --cpus)       CPUS="$2"; shift 2 ;;
    --mem)        MEM="$2"; shift 2 ;;
    --time)       TIME="$2"; shift 2 ;;
    --port)       PORT="$2"; shift 2 ;;
    --account)    ACCOUNT="$2"; shift 2 ;;
    --partition)  PARTITION="$2"; shift 2 ;;
    --dir)        NOTEBOOK_DIR="$2"; shift 2 ;;
    --env)        ENV_NAME="$2"; shift 2 ;;
    --login-host) LOGIN_HOST="$2"; shift 2 ;;
    -h|--help)
      grep '^#' "$0" | sed 's/^# \{0,1\}//' | sed '/^!/d'
      exit 0 ;;
    *)
      echo "Unknown option: $1" >&2
      echo "Try: $0 --help" >&2
      exit 1 ;;
  esac
done

# ------------------------------- sanity checks ------------------------------
command -v sbatch >/dev/null 2>&1 || {
  echo "ERROR: sbatch not found. Run this on a Slurm login node." >&2
  echo "       On a laptop just run:  conda activate ${ENV_NAME} && jupyter lab" >&2
  exit 1; }

# Find conda the same way setup_generic.sh does.
CONDA_SH=""
if [ -n "${CONDA_EXE:-}" ] && [ -f "$(dirname "$(dirname "$CONDA_EXE")")/etc/profile.d/conda.sh" ]; then
  CONDA_SH="$(dirname "$(dirname "$CONDA_EXE")")/etc/profile.d/conda.sh"
else
  for base in "$HOME/miniforge3" "$HOME/miniconda3" "$HOME/anaconda3" \
              /opt/conda /usr/local/miniconda3 /shared/software/miniconda; do
    [ -f "$base/etc/profile.d/conda.sh" ] && { CONDA_SH="$base/etc/profile.d/conda.sh"; break; }
  done
fi
[[ -n "$CONDA_SH" && -f "$CONDA_SH" ]] || {
  echo "ERROR: no conda found. Set CONDA_EXE to your conda binary and re-run." >&2; exit 1; }

source "$CONDA_SH"
conda env list | awk '{print $1}' | grep -qx "$ENV_NAME" || [ -d "$ENV_NAME" ] || {
  echo "ERROR: conda environment '$ENV_NAME' not found." >&2
  echo "       Create it first:  bash setup_generic.sh" >&2
  echo "       Or point at it:   $0 --env /full/path/to/env" >&2
  exit 1; }

# Slurm artifacts must live on a SHARED filesystem: node-local /tmp is invisible to
# the login node, so a job writing there cannot be reached.
case "$LOG_DIR$CONNECT_FILE" in
  /tmp/*) echo "ERROR: LOG_DIR/CONNECT_FILE must be on a shared filesystem, not /tmp." >&2; exit 1 ;;
esac
mkdir -p "$LOG_DIR"

# A token protects your server (anyone who reaches the port needs it). Fresh each launch.
TOKEN="$(python3 -c 'import secrets; print(secrets.token_hex(24))' 2>/dev/null \
         || openssl rand -hex 24 2>/dev/null \
         || head -c 24 /dev/urandom | od -An -tx1 | tr -d ' \n')"

JOB_OUT="$LOG_DIR/jupyter_%j.log"

SBATCH_EXTRA=()
[ -n "$ACCOUNT" ]   && SBATCH_EXTRA+=(--account="$ACCOUNT")
[ -n "$PARTITION" ] && SBATCH_EXTRA+=(--partition="$PARTITION")

# --------------------------- submit the Slurm job ---------------------------
JOBID="$(
sbatch --parsable \
  --job-name="jupyter" \
  "${SBATCH_EXTRA[@]}" \
  --cpus-per-task="$CPUS" \
  --mem="$MEM" \
  --time="$TIME" \
  --output="$JOB_OUT" \
  --error="$JOB_OUT" \
  --export=ALL,PORT="$PORT",JTOKEN="$TOKEN",CONNECT_FILE="$CONNECT_FILE",NOTEBOOK_DIR="$NOTEBOOK_DIR",CONDA_SH="$CONDA_SH",ENV_NAME="$ENV_NAME",LOGIN_HOST="$LOGIN_HOST" \
  <<'JOBEOF'
#!/usr/bin/env bash
set -eo pipefail

NODE="$(hostname -s)"
USER_NAME="${USER:-$(whoami)}"

source "$CONDA_SH"
conda activate "$ENV_NAME"

TUNNEL="ssh -N -L ${PORT}:${NODE}:${PORT} -J ${USER_NAME}@${LOGIN_HOST} ${USER_NAME}@${NODE}"
URL="http://localhost:${PORT}/lab?token=${JTOKEN}"

cat > "$CONNECT_FILE" <<INFO
============================================================
 Persistent JupyterLab server -- connection info
 (job ${SLURM_JOB_ID:-?}, written $(date '+%Y-%m-%d %H:%M:%S'))
============================================================
NODE  : ${NODE}
PORT  : ${PORT}
TOKEN : ${JTOKEN}

STEP 1 -- On your LAPTOP, open a terminal and run this (keep it open):

  ${TUNNEL}

STEP 2 -- In your browser on the laptop, open:

  ${URL}

Close your laptop any time. Your notebook and its running cells stay alive on
the compute node while this Slurm job runs. To get back in: re-run the STEP 1
tunnel command and reopen the STEP 2 URL -- you land on the SAME live kernels.

If STEP 1 fails, your cluster may not allow ProxyJump to compute nodes. Then use
two hops instead: ssh to the login node, and from there
  ssh -N -L ${PORT}:localhost:${PORT} ${NODE}
while tunnelling the login node's port to your laptop separately.

VS Code alternative (instead of the browser): command palette ->
"Jupyter: Specify Jupyter Server for Connections..." -> "Existing" -> paste:
  http://localhost:${PORT}/?token=${JTOKEN}
(the tunnel from STEP 1 must be running).

Check the job : squeue -u ${USER_NAME}
Stop  the job : scancel ${SLURM_JOB_ID:-<jobid>}
============================================================
INFO

echo "===================== JUPYTER CONNECTION INFO ====================="
cat "$CONNECT_FILE"
echo "==================================================================="
echo "Starting jupyter lab on ${NODE}:${PORT} ..."

cd "$NOTEBOOK_DIR"
exec jupyter lab \
  --no-browser \
  --ip=0.0.0.0 \
  --port="${PORT}" \
  --ServerApp.token="${JTOKEN}" \
  --ServerApp.root_dir="${NOTEBOOK_DIR}" \
  --ServerApp.allow_origin='*'
JOBEOF
)"

LOG_FILE="$LOG_DIR/jupyter_${JOBID}.log"

cat <<MSG

Submitted persistent JupyterLab job: ${JOBID}
  env=${ENV_NAME}  cpus=${CPUS}  mem=${MEM}  time=${TIME}  port=${PORT}
  partition=${PARTITION:-<cluster default>}  account=${ACCOUNT:-<none>}
  job log        : ${LOG_FILE}
  connection file: ${CONNECT_FILE}

NEXT STEPS
----------
1. Wait for the job to start (usually 10-60 s):
     squeue -u \$USER
   When state shows 'R' (running), continue.

2. Read the connection info the job wrote (node, port, token, tunnel, URL):
     cat ${CONNECT_FILE}
   (If it is not there yet, the job has not started -- wait and retry.)

3. Follow the two steps printed in that file.

RECONNECT AFTER CLOSING YOUR LAPTOP
-----------------------------------
The server and your running kernels stay alive as long as this Slurm job runs.
Re-run the SAME tunnel command and reopen the SAME URL. Nothing is lost.

STOP IT WHEN DONE
-----------------
  scancel ${JOBID}

MSG
