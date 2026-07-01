# `precomputed/` — GPU-step outputs (fetch separately; not in git)

The course server has **no GPU**, so the two GPU-heavy steps were run once and their outputs
saved here. The scVI cell (Level 1) and the three cell2location cells (Level 2) **load these
files instead of training** — that's the default (`TRAIN_SCVI = False` / `TRAIN_C2L = False` in
the notebooks). No student needs a GPU.

These files are **too large for git** (two are >100 MB), so they are git-ignored and must be
placed here out-of-band.

| File | ~Size | What it is |
|---|---|---|
| `level1_scvi_latent.npz` | 14 MB | scVI 30-dim latent (`X_scvi`, 117,200×30) + `obs_names` |
| `level2_c2l_ref_signatures.parquet` | 1.7 MB | cell2location reference signatures (`inf_aver`) |
| `level2_c2l_AT10_mapped.h5ad` | 776 MB | AT10 Visium mapped — abundance in `.obsm["q05_cell_abundance_w_sf"]` |
| `level2_c2l_AT14_mapped.h5ad` | 601 MB | AT14 Visium mapped — same structure |

## How to place them (instructor, one-time)

The notebooks reference these by absolute path
(`/shared/projects/tp_2630_ubordeaux_neuromics_184418/projects/C10/lederer/gbm_space_proj/precomputed/`),
so put the four files in that shared location and every student reads them there.

rsync from where they were generated (adjust the source host/path to yours):

```bash
DEST=/shared/projects/tp_2630_ubordeaux_neuromics_184418/projects/C10/lederer/gbm_space_proj/precomputed
rsync -avP <user>@<gpu-host>:/work/PRTNR/CHUV/DIR/rgottar1/single_cell_all/users/alederer/C10/lederer/gbm_space_proj/precomputed/ "$DEST"/
```

## Verify

From the project root, in the `single_cell` env:

```bash
python scratch_build/validate_precomputed.py
```

It loads all four files and checks shapes/alignment on CPU (no GPU, no training). If a student
sees `FileNotFoundError: Precomputed ... not found`, the files aren't in the path above (or the
path needs repointing for this server).
