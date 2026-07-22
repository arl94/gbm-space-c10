# Setup guide — C10 on any Slurm cluster

This is the cluster-agnostic version of `INSTALL.md`. The original is kept as a record of how
the course actually ran on the IFB Core cluster; it hardcodes that cluster's login host, Slurm
account and shared conda environment, so it only works there. This guide assumes nothing about
your site beyond "it has conda and Slurm".

Running on a **laptop** instead? Use [`docs/local_install_mac_windows.md`](docs/local_install_mac_windows.md).

Fill in these three things once and the rest of the guide follows:

| Placeholder | What it is | How to find it |
|---|---|---|
| `<LOGIN_HOST>` | the machine you SSH to | your site's documentation |
| `<PARTITION>` | a CPU partition/queue | `sinfo -s` |
| `<ACCOUNT>` | a billing account, **if your site requires one** | `sacctmgr show assoc user=$USER format=account,partition` |

---

## 1. Passwordless login with an SSH key

Typing your password on every connection gets old fast, and VS Code reconnects often.

```bash
# macOS / Linux, on your laptop:
ssh-keygen -t ed25519 -C "c10"          # press Enter at every prompt
ssh-copy-id <USER>@<LOGIN_HOST>

# Windows PowerShell (no ssh-copy-id):
ssh-keygen -t ed25519 -C "c10"
type $env:USERPROFILE\.ssh\id_ed25519.pub | ssh <USER>@<LOGIN_HOST> "mkdir -p ~/.ssh && cat >> ~/.ssh/authorized_keys && chmod 600 ~/.ssh/authorized_keys"
```

Test it: `ssh <USER>@<LOGIN_HOST>` should let you straight in.

Optionally add a shortcut to `~/.ssh/config` on your laptop so you can just type `ssh c10`:

```
Host c10
    HostName <LOGIN_HOST>
    User <USER>
```

## 2. VS Code, connected to the cluster

1. Install [VS Code](https://code.visualstudio.com/) and the **Remote - SSH**, **Python** and
   **Jupyter** extensions.
2. Command palette (`F1`) → *Remote-SSH: Connect to Host* → `c10`.
3. *File → Open Folder* → your home directory on the cluster.

Note what this does **not** give you: a VS Code window connected to the login node runs your
notebook kernel *on the login node*, with login-node memory limits and no scheduler. That is
fine for editing. For real compute, see §5.

## 3. Get the materials

```bash
git clone https://github.com/arl94/gbm-space-c10.git
cd gbm-space-c10
```

If you want to keep your own work under version control, fork the repo on GitHub first, clone
your fork, and add the original as `upstream` so you can pull updates:

```bash
git remote add upstream https://github.com/arl94/gbm-space-c10.git
git pull upstream master      # later, to get fixes
```

## 4. The environment

```bash
bash setup_generic.sh          # CPU -- the right choice unless you plan to retrain the GPU steps
bash setup_generic.sh --gpu    # CUDA, Linux x86-64 only
```

The script finds conda wherever your site keeps it (including behind `module load conda`),
creates the environment from `environment-cpu.yml`, verifies that every package the notebooks
import is present, and registers a Jupyter kernel.

Doing it by hand is two commands:

```bash
conda env create -f environment-cpu.yml
conda activate c10
```

If conda is only available after a module load, and `conda activate` complains that you must
run `conda init` first, this is the fix for the current shell:

```bash
source "$(dirname "$(dirname "$CONDA_EXE")")/etc/profile.d/conda.sh"
```

## 5. The data

```bash
bash scripts/fetch_c10_data.sh <bundle-location>
python scripts/check_c10_data.py       # must report 16/16
```

See [`data/README.md`](data/README.md) for what the bundle contains and where to get it.
Nothing else needs configuring: the notebooks resolve every path relative to the repository
root, so as long as `check_c10_data.py` passes, they will find their inputs.

## 6. Running notebooks with real memory — use Slurm, never the login node

Level 1 on the full 118,471-nucleus dataset peaks at about **23 GB RSS** and takes ~18 minutes
on 16 cores. Do not run that on a login node.

### Method A — a persistent Jupyter server inside a Slurm job (recommended)

```bash
./start_jupyter_generic.sh --partition <PARTITION> --mem 48G --cpus 16 --time 08:00:00
# add --account <ACCOUNT> if your site requires one
cat ~/jupyter_connect.txt          # once the job is running: node, port, token, tunnel command
```

The server lives inside the job, not inside your SSH session, so you can close your laptop and
reconnect to the same live kernels. The connection file tells you exactly what to run.

### Method B — VS Code attached directly to a compute node

```bash
salloc --partition <PARTITION> --cpus-per-task 16 --mem 48G --time 04:00:00
squeue -u $USER          # note the node name, e.g. node042
```

Then on your laptop add to `~/.ssh/config`:

```
Host c10-compute
    HostName node042
    User <USER>
    ProxyJump c10
```

and *Remote-SSH: Connect to Host* → `c10-compute`. Your kernel now runs on the allocated node.
Some sites forbid `ProxyJump` to compute nodes; if so, use Method A.

### Method C — batch execution, for long unattended runs

```bash
#!/bin/bash
#SBATCH --job-name=c10
#SBATCH --partition=<PARTITION>
#SBATCH --cpus-per-task=16
#SBATCH --mem=48G
#SBATCH --time=04:00:00
#SBATCH --output=%x_%j.log

source "$(dirname "$(dirname "$CONDA_EXE")")/etc/profile.d/conda.sh"
conda activate c10
cd ~/gbm-space-c10/notebooks/level1
jupyter nbconvert --to notebook --execute --inplace 01_snrna_analysis_student.ipynb
```

Two things that bite people here:

- **Do not use `set -u`** in a job script that activates conda. Some environments ship an
  activation hook that dereferences an unset `LD_LIBRARY_PATH`, and the job dies during
  `conda activate`. This project's own `scratch_build/run_level1_solution.sbatch` documents it.
- **Slurm artifacts must be on a shared filesystem.** Node-local `/tmp` is invisible to the
  login node; a job that writes its output there cannot be reached or read afterwards.

## 7. GPUs

You do not need one. The only GPU-accelerated steps are scVI (Level 1 §4) and cell2location
training (Level 2 §5), and both ship their full-scale outputs in `precomputed/`; the notebooks
load those by default. If you do want to train them, build the GPU environment
(`bash setup_generic.sh --gpu`), request a GPU partition, and set `TRAIN_SCVI = True` /
`TRAIN_C2L = True` in the relevant cell.

```bash
python -c "import torch; print(torch.cuda.is_available())"   # must print True
```

## Quick reference

```bash
conda activate c10                              # every new shell
python scripts/check_c10_data.py                # is the data in place?
squeue -u $USER                                 # my jobs
scancel <JOBID>                                 # stop one
sinfo -s                                        # what partitions exist
sacct -j <JOBID> --format=JobID,State,Elapsed,MaxRSS   # what a finished job actually used
```

## Troubleshooting

| Symptom | Cause and fix |
|---|---|
| `conda: command not found` | Your site hides it behind a module: `module load conda` (or `Anaconda3`). |
| `Run 'conda init' before 'conda activate'` | `source "$(dirname "$(dirname "$CONDA_EXE")")/etc/profile.d/conda.sh"` |
| `ModuleNotFoundError` in a notebook | Wrong kernel. In VS Code, *Select Kernel* → `Python (c10)`. |
| Kernel dies during Level 1 | Out of memory. It needs ~23 GB; request `--mem 48G`, or subsample. |
| `FileNotFoundError` on a `.h5ad` | Data not fetched. Run `python scripts/check_c10_data.py`. |
| CellTypist `FileNotFoundError: No such file` | Its model is not downloaded. The notebook's `models.download_models(...)` call needs network access — run that cell once on a node that has it. |
| Job pending forever | Usually an over-large request. Ask for what you need (48G, not 200G) and check `sinfo -s`. |
