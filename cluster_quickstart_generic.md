# Cluster quickstart — VS Code, passwordless login, conda

A short setup for working on **any Slurm cluster** from **VS Code**. Do this once; it applies to
any project. About 15 minutes.

This is the cluster-agnostic version of `cluster_quickstart.md`, which is kept as a record of the
IFB Core setup the course actually used. Substitute your own values for:

| Placeholder | How to find it |
|---|---|
| `<LOGIN_HOST>` | your site's documentation |
| `<USER>` | your username on the cluster |
| `<PARTITION>` | `sinfo -s` |

For the full C10 setup (environment, data, running notebooks with real memory) continue with
[`INSTALL_generic.md`](INSTALL_generic.md). On a laptop, use
[`docs/local_install_mac_windows.md`](docs/local_install_mac_windows.md) instead.

---

## 1. Install VS Code + the Remote-SSH extension

1. Install **VS Code** on your laptop: <https://code.visualstudio.com/>
2. Extensions panel (`Ctrl/Cmd+Shift+X`) → install **Remote - SSH** (Microsoft).

The **Python** and **Jupyter** extensions come later, installed on the cluster side in step 5.

---

## 2. Passwordless login with an SSH key

**a. Make a key** (skip if `~/.ssh/id_ed25519` already exists), in a laptop terminal:

```bash
ssh-keygen -t ed25519          # press Enter through the prompts
```

**b. Copy the public key to the cluster** (asks for your password one last time):

```bash
# macOS / Linux:
ssh-copy-id <USER>@<LOGIN_HOST>

# Windows PowerShell (no ssh-copy-id):
type $env:USERPROFILE\.ssh\id_ed25519.pub | ssh <USER>@<LOGIN_HOST> "mkdir -p ~/.ssh && cat >> ~/.ssh/authorized_keys && chmod 600 ~/.ssh/authorized_keys"
```

**c. Add a shortcut.** Open `~/.ssh/config` (in VS Code: `F1` → "Remote-SSH: Open SSH
Configuration File") and add:

```
Host mycluster
    HostName <LOGIN_HOST>
    User <USER>
    IdentityFile ~/.ssh/id_ed25519
```

**d. Test — this should log in with no password:**

```bash
ssh mycluster
```

> Still asking for a password? On the cluster run `chmod 700 ~/.ssh && chmod 600 ~/.ssh/authorized_keys`.
> If you gave the key a passphrase you will be asked for *that* (not your account password);
> `ssh-add ~/.ssh/id_ed25519` caches it for the session.

---

## 3. Connect VS Code to the cluster

1. `F1` → **Remote-SSH: Connect to Host...** → **`mycluster`**. No password prompt.
2. **File → Open Folder...** to open your working directory on the cluster.

---

## 4. Get conda working

Conda lives in a different place on every cluster. Try these in order:

```bash
conda --version                     # already on PATH? done
module load conda                   # or: module load Anaconda3 / miniconda
ls /opt/conda /shared/software/miniconda ~/miniforge3 ~/miniconda3 2>/dev/null
```

If `conda activate` complains *"Run 'conda init' before 'conda activate'"* — a very common
first-time error — either fix it for the current shell:

```bash
source "$(dirname "$(dirname "$CONDA_EXE")")/etc/profile.d/conda.sh"
```

or permanently, which edits your `~/.bashrc`:

```bash
conda init bash        # then open a NEW terminal
```

No conda at all? Install Miniforge into your home directory:
<https://conda-forge.org/download/>.

Sanity check with a throwaway environment:

```bash
conda create -n hello python=3.11 -y
conda activate hello
python -c "print('conda works')"
conda deactivate && conda env remove -n hello -y
```

> Rule of thumb: the login node is for editing and light setup only. Anything heavy — training,
> a full dataset, a long analysis — goes through Slurm. Sites monitor this, and a big job on a
> login node affects everyone.

---

## 5. Python and Jupyter in VS Code

With VS Code **connected to the cluster** (not on your laptop), install into the remote:

- **Python** (Microsoft)
- **Jupyter** (Microsoft)

They install on the cluster side, which is what you want — the "Install in SSH: mycluster"
button is the one to press.

Then open any `.ipynb`, click **Select Kernel** (top right) → **Python Environments** → your
environment. If it does not appear, register it explicitly:

```bash
conda activate <your-env>
python -m ipykernel install --user --name <your-env> --display-name "Python (<your-env>)"
```

---

## 6. Check Slurm works

```bash
sinfo -s                                  # partitions, and how busy they are
squeue -u $USER                           # your jobs (probably none yet)
srun --partition <PARTITION> --time 00:05:00 --mem 4G hostname
```

That last command should print the name of a compute node. If it complains about an account,
your site requires one:

```bash
sacctmgr show assoc user=$USER format=account,partition
```

and you then pass `--account <ACCOUNT>` to every job.

---

## Quick reference

```bash
ssh mycluster                             # log in
conda activate <your-env>                 # every new shell
sinfo -s                                  # partitions
squeue -u $USER                           # my jobs
scancel <JOBID>                           # stop one
sacct -j <JOBID> --format=JobID,State,Elapsed,MaxRSS   # what it actually used
```
