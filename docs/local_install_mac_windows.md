# Running the C10 project locally in VS Code (macOS & Windows)

This guide installs the `c10` conda environment on your **own laptop** (CPU-only)
and runs the project notebooks in **VS Code**. It works on macOS (Intel or Apple Silicon)
and Windows.

---

## Read this first — what "local" can and can't do

- **Use `environment-cpu.yml`.** It installs the same libraries at the same versions the
  solution notebooks were executed with, but with a CPU build of PyTorch, and it is verified to
  solve on macOS (Intel and Apple Silicon), Windows and Linux. `environment-gpu.yml` is the
  CUDA variant and is Linux x86-64 only. `single_cell_environment.yml` is a frozen `pip freeze`
  of the instructor's cluster environment, kept only as a record of exactly what produced the
  published outputs — it contains Linux-only packages and **will fail to install on
  macOS/Windows**.
- **No GPU locally = the heavy training steps are slow.** Two steps were built for a GPU:
  Level 1's scVI integration and Level 2's cell2location deconvolution. On a laptop CPU they
  can take a very long time (or run out of RAM). You usually **don't need to re-run them** —
  the repo ships their outputs under `precomputed/`:
  - `precomputed/level1_scvi_latent.npz` — Level 1 scVI latent space
  - `precomputed/level2_c2l_AT10_mapped.h5ad`, `level2_c2l_AT14_mapped.h5ad` — Level 2 cell2location maps
  - `precomputed/level2_c2l_ref_signatures.parquet` — the reference signatures
  The notebooks are written to **load these instead of training** where possible.
  (Apple Silicon: PyTorch's MPS backend is not reliably supported by scvi-tools/cell2location —
  stick to CPU.)
- **You need the data, and it's large.** Fetch it with `scripts/fetch_c10_data.sh` (Step 5):
  a 5.1 GB download that decompresses to 11.7 GB. Paths are relative to the repository, so
  there is nothing to edit afterwards.
- **RAM is the real constraint.** Level 1 on the full 118,471-nucleus dataset peaks at about
  **23 GB RSS** (measured: 16 cores, ~18 min). **32 GB RAM is the comfortable minimum.** On a
  16 GB machine Level 1 will swap-thrash or be killed, most often during highly-variable-gene
  selection, PCA or inferCNV — subsample first (see "Working with less than 32 GB" below).
  Levels 1b, 2 and 3 are much lighter and are fine on 16 GB.
- **Disk:** ~15 GB for the data plus ~4 GB for the environment.

---

## Step 0 — Install Miniforge (conda)

Miniforge is a minimal conda pre-configured for the `conda-forge` channel (what this project
uses). If you already have Miniconda/Anaconda, that's fine too — just make sure `conda-forge`
is available.

**macOS**
1. Download the installer for your chip from <https://github.com/conda-forge/miniforge#install>
   (Apple Silicon → `arm64`; Intel → `x86_64`), or in Terminal:
   ```bash
   curl -L -O "https://github.com/conda-forge/miniforge/releases/latest/download/Miniforge3-$(uname)-$(uname -m).sh"
   bash Miniforge3-$(uname)-$(uname -m).sh
   ```
2. Close and reopen Terminal, then confirm: `conda --version`

**Windows**
1. Download **Miniforge3 Windows x86_64** `.exe` from the link above and run it (accept defaults;
   "Just Me" is fine).
2. Open **"Miniforge Prompt"** from the Start menu (use this for all conda commands below).
   Confirm: `conda --version`

---

## Step 1 — Get the project repository

Clone it (or copy the folder to your laptop). Pick a path **without spaces**.

**macOS (Terminal)**
```bash
cd ~/projects            # or wherever you keep code
git clone <REPO_URL> gbm-space-c10
cd gbm-space-c10
```

**Windows (Miniforge Prompt)**
```bat
cd %USERPROFILE%\projects
git clone <REPO_URL> gbm-space-c10
cd gbm-space-c10
```

> If you don't have the Git URL, just copy the `gbm-space-c10` folder onto your laptop and
> `cd` into it.

---

## Step 2 — Create the conda environment

From inside the repo folder (so it can see `environment-cpu.yml`):

```bash
conda env create -f environment-cpu.yml
conda activate c10
```

This takes 10–20 minutes and downloads a few GB. If the solve is very slow, speed it up with
the faster solver (already default in recent conda; otherwise):
```bash
conda install -n base conda-libmamba-solver
conda config --set solver libmamba
```

Then register the environment as a Jupyter kernel so VS Code can find it:
```bash
python -m ipykernel install --user --name c10 --display-name "Python (c10)"
```

Quick sanity check (should print versions and `CUDA available: False`):
```bash
python -c "import scanpy, torch, squidpy, cell2location; print('scanpy', scanpy.__version__, '| CUDA available:', torch.cuda.is_available())"
```

### Step 2 (alternative) — do it in the Anaconda Navigator GUI

If you prefer clicking to typing, you can create the environment from the same file in
**Anaconda Navigator** (no terminal needed):

1. Open **Anaconda Navigator** → **Environments** tab (left).
2. Click **Import** (bottom of the environment list).
3. In the dialog: **Name** = `c10`; under **Import from** choose **Local drive** and
   browse to `environment-cpu.yml` in the repo. Leave "New environment name" as `c10`.
   Click **Import**.
4. Navigator now runs the install (this is the same as `conda env create`). The **pip phase
   near the end is long and the progress bar may look stuck for several minutes** — that's
   normal; let it finish.
5. When done, `c10` appears in the environment list. `ipykernel` is already included,
   so VS Code will detect it — but if the kernel doesn't show up later, select `c10`
   in Navigator's environment list, click the ▶ button → **Open Terminal**, and run:
   ```bash
   python -m ipykernel install --user --name c10 --display-name "Python (c10)"
   ```

Notes / caveats for the Navigator route:
- Use a **recent** Navigator — older versions can't import a YAML that has a `pip:` section.
- Navigator's Import is all-or-nothing and gives little feedback if a pip package fails. **If
  the import errors out, fall back to the command line** (`conda env create -f environment-cpu.yml`),
  which shows exactly what went wrong.
- You can also launch tools from Navigator's **Home** tab: set **"Applications on" → `c10`**
  at the top, then launch **VS Code** (or JupyterLab) already pointed at that environment.

### Working entirely in Anaconda Navigator (no command line at all)

Students can do the whole course from Navigator. **Put the repo somewhere under your home
folder first** (e.g. `~/projects/gbm-space-c10` on macOS, `C:\Users\<you>\projects\gbm-space-c10`
on Windows) — JupyterLab can only browse folders at or below where it launches, and Navigator
launches from your home folder.

1. Create the environment via **Environments → Import** (Step 2 alternative, above).
2. Go to the **Home** tab. At the top, set **"Applications on"** to **`c10`**. Every
   app you launch from now on uses that environment.
3. Launch one of:
   - **JupyterLab** (fully inside the Anaconda ecosystem, recommended for students) — click
     **Launch** under JupyterLab. It opens in your browser. In the left file browser, navigate
     into `gbm-space-c10/notebooks/…` and double-click a notebook. Because it launched from the
     `c10` env, the kernel is already correct (top-right shows **Python 3 (ipykernel)**
     running in `c10`). Run cells with **Shift+Enter**.
   - **VS Code** — click **Launch** (Navigator installs the integration the first time). Then
     **File → Open Folder →** the repo, open a notebook, and **Select Kernel → `c10`**
     (as in Steps 3–4).
4. **Repoint the data paths** (Step 5) and run. This is the same regardless of which app you launch.

> Tip for students: **JupyterLab from Navigator** is the least-moving-parts option — no kernel
> picker, no interpreter selection, no extensions to install. VS Code is nicer for editing and
> debugging but has the extra kernel-selection step. Either works with the same environment.

---

## Step 3 — Install VS Code and its extensions

1. Install **VS Code**: <https://code.visualstudio.com/>
2. In VS Code, open the **Extensions** panel (square icon on the left) and install:
   - **Python** (Microsoft)
   - **Jupyter** (Microsoft)
3. Open the project: **File → Open Folder…** → select your `gbm-space-c10` folder.

---

## Step 4 — Select the `c10` kernel

1. Open a notebook, e.g. `notebooks/level1/01_snrna_analysis_student.ipynb`.
2. Top-right of the notebook, click **Select Kernel** → **Python Environments…** →
   choose **`c10`** (the one you created; display name "Python (c10)").
   - If it doesn't appear, run **Command Palette (Cmd/Ctrl+Shift+P) → "Python: Select
     Interpreter"** and pick the `c10` conda env, then reopen the notebook.
3. Run the first (setup) cell. `import` errors here mean the kernel isn't the `c10`
   env — recheck the kernel picker.

---

## Step 5 — Fetch the data

The notebooks resolve every path relative to the repository root, so there is nothing to edit.
Get the datasets into place and they will be found:

```bash
bash scripts/fetch_c10_data.sh <bundle-location>
python scripts/check_c10_data.py        # must report 16/16 present
```

`<bundle-location>` is wherever you downloaded the C10 data bundle to. See
[`../data/README.md`](../data/README.md) for what it contains and where to get it. If you keep
the data somewhere other than the repository, set `C10_ROOT` to the repository path instead.

> **Minimum to get going:** Level 1 needs the snRNA `.h5ad`; Level 2 loads the `precomputed/`
> cell2location maps instead of training; Level 3 needs the Xenium `_annotated.h5ad` files, and
> the `transcripts.parquet` tables only for the nuclear-vs-cytoplasmic section.

---

## Working with less than 32 GB of RAM

Level 1 is the only heavy notebook. To run it on a smaller machine, subsample right after the
load cell in Section 1 and continue as normal — every later step scales down with it:

```python
import scanpy as sc
sc.pp.subsample(adata, n_obs=30_000, random_state=0)   # ~6 GB instead of ~23 GB
```

Your cluster numbers and cell-type proportions will differ slightly from the answer key, which
is expected and worth noticing. The Level 1 output that Levels 1b/2/3 consume also ships
pre-built in the data bundle, so you can subsample freely without breaking the later notebooks.

---

## Troubleshooting

| Symptom | Fix |
|---|---|
| `conda env create` fails to solve / "PackagesNotFound", Linux/CUDA names | You used `single_cell_environment.yml`. Use **`environment-cpu.yml`**. |
| Solve takes forever | `conda install -n base conda-libmamba-solver` then `conda config --set solver libmamba`. |
| `No module named 'skmisc'` (seurat_v3 HVGs) | It's included here (`scikit-misc`). Confirm the `c10` kernel is selected. |
| `torch.cuda.is_available()` is `False` | Expected — this is a CPU-only laptop env. |
| Apple Silicon build/wheel errors | Make sure you installed the **arm64** Miniforge, then recreate the env. |
| VS Code can't see the kernel | Re-run the `ipykernel install` line in Step 2, then "Python: Select Interpreter". |
| Kernel dies / machine swaps during Level 1 | Out of RAM. It needs ~23 GB. Subsample — see "Working with less than 32 GB". |
| CellTypist `FileNotFoundError: No such file` | Its model downloads on first use and needs network access. Re-run that cell while online. |
| A training cell (scVI / cell2location) runs forever or hits memory | Skip it — load the matching file from `precomputed/` (see top of this doc). |
| `FileNotFoundError` on a data path | The data is not fetched. Run `python scripts/check_c10_data.py`. |

---

## TL;DR

```bash
# 0. install Miniforge (see Step 0)
# 1. get the repo
git clone <REPO_URL> gbm-space-c10 && cd gbm-space-c10
# 2. create + activate the CPU env
conda env create -f environment-cpu.yml
conda activate c10
python -m ipykernel install --user --name c10 --display-name "Python (c10)"
# 3. install VS Code + Python + Jupyter extensions, open the folder
# 4. get the data -- paths need no editing
bash scripts/fetch_c10_data.sh <bundle-location> && python scripts/check_c10_data.py
# 5. open a notebook, Select Kernel -> c10, and run
```
