# GBM-Space C10 — project context for Claude

The CAJAL "Neuromics 2026" course project **C10** (spatial transcriptomics of glioblastoma).
Developed on the UNIL/CHUV **Curnagl** cluster, run on **IFB Core** for the course itself.

**The course is over (July 2026).** The repository has been turned into a public, self-contained
release: solutions ship alongside the student notebooks as answer keys, and every path is
repo-relative. Read `README.md` first — it is now the student-facing entry point.

## What this project is

Students reproduce, from scratch, the findings of a glioblastoma paper (de Jong, Memi, Gracia,
Lazareva et al., bioRxiv 2025.05.13.653495; gbmspace.org), across four notebooks:

- **Level 1** (`notebooks/level1/`): snRNA-seq — QC, integration (Harmony + scVI), CellTypist
  annotation, inferCNV malignant/TME split, malignant cell-state axis.
  In: `data/snRNA_seq/level1_prepared/gbm_l1_snrna_AT10_AT14_raw.h5ad` (118,471 nuclei).
  Out: `data/processed/gbm_l1_snrna_AT10_AT14_annotated.h5ad` — the input to 1b, 2 and 3.
- **Level 1b** (`notebooks/level1b/`): read the paper, test five of its snRNA-only claims.
- **Level 2** (`notebooks/level2/`): Visium — QC, naive domains, axis-in-space, **cell2location**
  deconvolution, NMF niches, squidpy/k-d-tree neighborhoods, LIANA, AT14 cross-tumor comparison,
  answer-key comparison + write-up.
- **Level 3** (`notebooks/level3/`): Xenium organoids — single-cell spatial, neighborhoods,
  cross-modality comparison, per-molecule nuclear vs cytoplasmic analysis.

Each level is a `*_student.ipynb` / `*_solution.ipynb` pair in the same folder.

## Layout and path conventions

Every notebook's **first code cell** is a PROVIDED project-paths cell: it walks up from `Path.cwd()`
to the repo root (identified by `src/gbmspace_utils`), honors a `C10_ROOT` env override, and defines
`PROJECT_ROOT`, `NOTEBOOK_DIR`, `DATA_DIR`, `PRECOMP_DIR`, `REFERENCE_DIR`. **No absolute path may
appear in any notebook or script source.** Verify with:

```bash
grep -rn '/shared/projects\|/work/PRTNR' notebooks/ scripts/ src/   # must return nothing
python scripts/check_c10_data.py                                    # all 16 inputs resolve
```

Docs and markdown still mention both clusters deliberately, as migration history.

## Data

Datasets are not in git. `scripts/c10_data_manifest.txt` is the authoritative list of every file a
notebook opens (16 inputs, ~15 GB on disk, ~6 GB transferred gzipped); `scripts/fetch_c10_data.sh`
rsyncs and decompresses them; `scripts/check_c10_data.py` verifies. `data/README.md` explains each
file and what is deliberately excluded (the ~40 GB of raw Xenium morphology/zarr, the full Visium
cohort, the per-donor snRNA splits). The Curnagl staging bundle lives at
`/work/PRTNR/CHUV/DIR/rgottar1/single_cell_all/users/alederer/GBM_Space/c10_bundle/`.

`notebooks/level3/04_xenium_segmentation_basis_solution.ipynb` is gitignored and excluded from the
release: it needs the full raw Xenium folders and was never finished.

## Environment

Native conda env `single_cell` (no container). Spec: `single_cell_environment.yml`. Python 3.11 +
pip (torch, scvi-tools, cell2location, squidpy, LIANA, infercnvpy, celltypist).
**pip rule on shared clusters: always `pip install --no-user`** — a plain `pip install` can write to
`~/.local` and break other envs.

The two GPU steps (scVI, cell2location) are optional; their outputs ship in `precomputed/` and the
notebooks load them by default.

## Notebook generation (don't hand-edit notebooks)

- Solutions are built by `scratch_build/build_solution_nb*.py` and executed by
  `scratch_build/direct_execute_nb.py <nb> <timeout_s>` — an in-process executor that saves after
  every cell. It strips `%` line-magics but **not** `!` shell escapes, and it `exec()`s each cell,
  so bare IPython auto-magics (`pwd`, `ls`) are syntax errors under it.
- Students notebooks come from `scratch_build/derive_student_nb*.py`: keeps all markdown, blanks all
  code, and strips `<!-- INSTRUCTOR-ONLY -->…<!-- /INSTRUCTOR-ONLY -->` regions. Those sentinels have
  now been *removed* from the solutions (the wrapped text is the published answer), so re-deriving a
  student notebook from a current solution would leak the answers. Derive from the pre-release tag
  `pre-cleanup-2026-07-22` if you ever need to.
- To re-execute the Level 1 answer key: `sbatch scratch_build/run_level1_solution.sbatch`
  (16 CPU / 96 GB / partition `cpu`; ~40 GB peak RSS). Note the script must not use `set -u` — the
  env's `activate.d/basis_tbb_fix.sh` hook dereferences an unset `LD_LIBRARY_PATH`.

## Key gotchas already solved (detail in docs/build_notes.md + full_scale_run_plan.md)

- cell2location's reference label must be the real malignant cell-*state* clusters
  (`malignant_state`, 9 categories, + TME `cell_type`), NOT CellTypist's region-confounded mimic
  labels — the latter produce flat, uninformative maps. Mapping `batch_size` ≈ 25% of spots, and
  guard the last mini-batch of size 1 (`if n_obs % bs == 1: bs += 1`) or PyTorch crashes on a 0-d
  tensor.
- inferCNV `window_size=250` (paper-faithful); the malignant split is calibrated from per-cell
  signal, not an absolute `cnv_score` threshold.
- CellTypist's `Developing_Human_Brain.pkl` model must already be in `~/.celltypist/data/models/`;
  compute nodes may have no outbound network.

Session-by-session detail and the rich project memory are in `docs/session_memory/`.
