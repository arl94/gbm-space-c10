# GBM-Space Computational Mini-Project (C10)

Course material for CAJAL **Neuromics 2026**, project **C10**: reproduce, from scratch, the
spatial-transcriptomics findings of a glioblastoma study using real snRNA-seq, Visium and
Xenium data.

Source paper: de Jong, Memi, Gracia, Lazareva et al., bioRxiv 2025.05.13.653495 —
[gbmspace.org](https://www.gbmspace.org/).

> **The course is over, so this repository now ships the answer keys.** Each level has a
> `*_student.ipynb` (the notebook you worked through, code blanked) and a matching
> `*_solution.ipynb` (every cell filled in and executed, with the interpretation text that was
> hidden during the course). Read the solution *after* you have had a real go at the student
> version — the reasoning is the point, not the final numbers.

## Levels

| Level | Notebooks | What you do | Data |
|---|---|---|---|
| **1** | `notebooks/level1/01_snrna_analysis_*` | snRNA-seq on donors AT10 + AT14 (118,471 nuclei, no subsampling): QC, normalization, integration (Harmony *and* scVI, compared), clustering, cell-type annotation (markers + CellTypist), malignant/TME calling with inferCNV, and the paper's 4-state malignant cell axis (OPC-NPC-like / NPC-neuronal-like / AC-gliosis-hypoxia / Proliferative). | `data/snRNA_seq/level1_prepared/` |
| **1b** | `notebooks/level1b/01b_paper_hypotheses_*` | Read the paper, then test five of its snRNA-only claims against the reference *you* built in Level 1. | Level 1's output |
| **2** | `notebooks/level2/02_spatial_cell2location_*` | Visium on the matched AT10 section: spatial QC, naive domains, the cell-state axis in space, **cell2location** deconvolution of the Level 1 reference, NMF niches, squidpy/k-d-tree neighborhoods, LIANA cell-cell communication, the answer-key comparison and the AT14 cross-tumor check. | `data/visium/level2_prepared/` |
| **3** | `notebooks/level3/03_xenium_organoid_*` | Xenium on three organoid sections: single-cell spatial analysis, niche and neighborhood composition, cross-modality comparison against Levels 1–2, and a per-molecule look at nuclear vs cytoplasmic transcripts. | `data/xenium/` |

Level 1 writes `data/processed/gbm_l1_snrna_AT10_AT14_annotated.h5ad`, the input to Levels 1b, 2
and 3. It also ships pre-built in the data bundle, so any level can be run on its own.

**A note on Level 3.** Unlike the other levels, `03_xenium_organoid_student.ipynb` is not a blanked
exercise — 23 of its 24 code cells are identical to the solution and it ships already executed. It
is a condensed guided walkthrough rather than something to fill in; the `_solution` notebook is the
longer version, with the full analysis and commentary.

## Getting started

```bash
git clone https://github.com/arl94/gbm-space-c10.git
cd gbm-space-c10

conda env create -f single_cell_environment.yml     # or activate the shared `single_cell` env
conda activate single_cell

bash scripts/fetch_c10_data.sh                      # ~6 GB transfer, resumable
python scripts/check_c10_data.py                    # confirms all 16 inputs are in place

jupyter lab notebooks/level1
```

Longer setup notes, including VS Code Remote-SSH and running Jupyter on a compute node, are in
[`INSTALL.md`](INSTALL.md); local Mac/Windows installs in
[`docs/local_install_mac_windows.md`](docs/local_install_mac_windows.md).

### Paths

Every notebook opens with a **project-paths** cell that walks up from the working directory to the
repository root and derives `DATA_DIR`, `PRECOMP_DIR`, `REFERENCE_DIR` and `NOTEBOOK_DIR` from it.
Nothing is hardcoded, so the notebooks run from any checkout location. If you keep the datasets
elsewhere, set `C10_ROOT` to the repository path and everything follows.

### GPU steps

Exactly two steps want a GPU: **scVI** integration (Level 1 §4) and **cell2location** training
(Level 2 §5). Both are optional — their full-scale outputs ship in `precomputed/` and the notebooks
load those by default (`TRAIN_SCVI = False`, `TRAIN_C2L = False`). Flip either flag to train it
yourself. Everything else runs on CPU.

## Repository layout

```
notebooks/level{1,1b,2,3}/   student + solution notebook per level
src/gbmspace_utils/          shared helpers the notebooks import (markers, scoring, plotting)
scripts/                     data prep (01, 02), a cell2location timing probe (03),
                             and the data fetch + check tooling
reference/                   GRCh38 gene positions for inferCNV
data/                        fetched separately -- see data/README.md
precomputed/                 GPU-step outputs, fetched with the data
docs/                        build notes, session history, setup notes, slides
```

## What is not included

- **`notebooks/level3/04_xenium_segmentation_basis_solution.ipynb`** — a BASIS re-segmentation
  notebook. It needs the complete raw Xenium output folders (~40 GB of morphology TIFFs and zarr
  stores) that the data bundle leaves out, and it was only ever partially executed. It stays on
  Curnagl.
- The instructor-side source data behind `scripts/01` and `scripts/02` (the per-donor snRNA files
  and the full 30-section Visium cohort). See [`data/README.md`](data/README.md) for where it lives.

## History

The project was developed on the UNIL/CHUV **Curnagl** cluster, then transferred to the **IFB Core**
cluster where the course actually ran; `docs/ifb_setup_notes.md` and `docs/full_scale_run_plan.md`
record that migration. Those notes are kept as history — the code itself no longer refers to either
cluster.
