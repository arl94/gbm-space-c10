# Running the C10 project locally in VS Code (macOS & Windows)

This guide installs the `single_cell` conda environment on your **own laptop** (CPU-only)
and runs the project notebooks in **VS Code**. It works on macOS (Intel or Apple Silicon)
and Windows.

---

## Read this first — what "local" can and can't do

- **Use `environment-local.yml`, NOT `single_cell_environment.yml`.** The latter is a frozen
  export from the Linux GPU cluster: it contains Linux-only packages and CUDA/NVIDIA builds
  of PyTorch and **will fail to install on macOS/Windows**. `environment-local.yml` installs
  the same libraries (same versions) with a CPU build of PyTorch.
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
- **You need the data, and it's large.** The notebooks reference dataset paths on the cluster.
  To actually run them you must copy the data to your laptop and repoint those paths
  (Step 5). The Xenium raw outputs alone are several GB each, so copy only what you need.
- **Recommended:** ≥16 GB RAM and ~15 GB free disk (env ≈ 6 GB + data).

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

From inside the repo folder (so it can see `environment-local.yml`):

```bash
conda env create -f environment-local.yml
conda activate single_cell
```

This takes 10–20 minutes and downloads a few GB. If the solve is very slow, speed it up with
the faster solver (already default in recent conda; otherwise):
```bash
conda install -n base conda-libmamba-solver
conda config --set solver libmamba
```

Then register the environment as a Jupyter kernel so VS Code can find it:
```bash
python -m ipykernel install --user --name single_cell --display-name "Python (single_cell)"
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
3. In the dialog: **Name** = `single_cell`; under **Import from** choose **Local drive** and
   browse to `environment-local.yml` in the repo. Leave "New environment name" as `single_cell`.
   Click **Import**.
4. Navigator now runs the install (this is the same as `conda env create`). The **pip phase
   near the end is long and the progress bar may look stuck for several minutes** — that's
   normal; let it finish.
5. When done, `single_cell` appears in the environment list. `ipykernel` is already included,
   so VS Code will detect it — but if the kernel doesn't show up later, select `single_cell`
   in Navigator's environment list, click the ▶ button → **Open Terminal**, and run:
   ```bash
   python -m ipykernel install --user --name single_cell --display-name "Python (single_cell)"
   ```

Notes / caveats for the Navigator route:
- Use a **recent** Navigator — older versions can't import a YAML that has a `pip:` section.
- Navigator's Import is all-or-nothing and gives little feedback if a pip package fails. **If
  the import errors out, fall back to the command line** (`conda env create -f environment-local.yml`),
  which shows exactly what went wrong.
- You can also launch tools from Navigator's **Home** tab: set **"Applications on" → `single_cell`**
  at the top, then launch **VS Code** (or JupyterLab) already pointed at that environment.

### Working entirely in Anaconda Navigator (no command line at all)

Students can do the whole course from Navigator. **Put the repo somewhere under your home
folder first** (e.g. `~/projects/gbm-space-c10` on macOS, `C:\Users\<you>\projects\gbm-space-c10`
on Windows) — JupyterLab can only browse folders at or below where it launches, and Navigator
launches from your home folder.

1. Create the environment via **Environments → Import** (Step 2 alternative, above).
2. Go to the **Home** tab. At the top, set **"Applications on"** to **`single_cell`**. Every
   app you launch from now on uses that environment.
3. Launch one of:
   - **JupyterLab** (fully inside the Anaconda ecosystem, recommended for students) — click
     **Launch** under JupyterLab. It opens in your browser. In the left file browser, navigate
     into `gbm-space-c10/notebooks/…` and double-click a notebook. Because it launched from the
     `single_cell` env, the kernel is already correct (top-right shows **Python 3 (ipykernel)**
     running in `single_cell`). Run cells with **Shift+Enter**.
   - **VS Code** — click **Launch** (Navigator installs the integration the first time). Then
     **File → Open Folder →** the repo, open a notebook, and **Select Kernel → `single_cell`**
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

## Step 4 — Select the `single_cell` kernel

1. Open a notebook, e.g. `notebooks/level1/01_snrna_analysis_student.ipynb`.
2. Top-right of the notebook, click **Select Kernel** → **Python Environments…** →
   choose **`single_cell`** (the one you created; display name "Python (single_cell)").
   - If it doesn't appear, run **Command Palette (Cmd/Ctrl+Shift+P) → "Python: Select
     Interpreter"** and pick the `single_cell` conda env, then reopen the notebook.
3. Run the first (setup) cell. `import` errors here mean the kernel isn't the `single_cell`
   env — recheck the kernel picker.

---

## Step 5 — Point the notebooks at your local data (required to run)

The notebooks were written with **absolute cluster paths**. Near the top of each notebook
there is a setup/paths cell defining variables you must change to where you put the data
locally. Look for:

- `sys.path.insert(0, "…/src")` — set this to your local repo's `src` folder, e.g.
  - macOS: `sys.path.insert(0, "/Users/<you>/projects/gbm-space-c10/src")`
  - Windows: `sys.path.insert(0, r"C:\Users\<you>\projects\gbm-space-c10\src")`
- Level 2: `VISIUM`, `VISIUM_AT14`, `ref_path`, the answer-key path
- Level 3: `XENIUM_DIR`, and the Level 1/Visium paths in the cross-modality section

Put the data under the repo's `data/` folder and point the variables there. Windows tip: use
raw strings (`r"C:\path\..."`) or forward slashes (`"C:/path/..."`) to avoid backslash-escape
issues; `pathlib.Path` (already used in the notebooks) handles both.

> **Minimum to get going:** Level 1 needs the snRNA `.h5ad`; Level 2 can load the
> `precomputed/` cell2location maps instead of training; Level 3 needs the Xenium
> `_annotated.h5ad` files (and the raw `transcripts.parquet` folders only for the
> nuclear-vs-cytoplasmic and niche sections).

---

## Troubleshooting

| Symptom | Fix |
|---|---|
| `conda env create` fails to solve / "PackagesNotFound", Linux/CUDA names | You used `single_cell_environment.yml`. Use **`environment-local.yml`**. |
| Solve takes forever | `conda install -n base conda-libmamba-solver` then `conda config --set solver libmamba`. |
| `No module named 'skmisc'` (seurat_v3 HVGs) | It's included here (`scikit-misc`). Confirm the `single_cell` kernel is selected. |
| `torch.cuda.is_available()` is `False` | Expected — this is a CPU-only laptop env. |
| Apple Silicon build/wheel errors | Make sure you installed the **arm64** Miniforge, then recreate the env. |
| VS Code can't see the kernel | Re-run the `ipykernel install` line in Step 2, then "Python: Select Interpreter". |
| A training cell (scVI / cell2location) runs forever or hits memory | Skip it — load the matching file from `precomputed/` (see top of this doc). |
| `FileNotFoundError` on a data path | You still have a cluster path — repoint it (Step 5). |

---

## TL;DR

```bash
# 0. install Miniforge (see Step 0)
# 1. get the repo
git clone <REPO_URL> gbm-space-c10 && cd gbm-space-c10
# 2. create + activate the CPU env
conda env create -f environment-local.yml
conda activate single_cell
python -m ipykernel install --user --name single_cell --display-name "Python (single_cell)"
# 3. install VS Code + Python + Jupyter extensions, open the folder
# 4. open a notebook, Select Kernel -> single_cell
# 5. edit the paths cell to your local data, then run
```
