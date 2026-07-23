# `precomputed/` — GPU-step outputs

Two steps in this project want a GPU: **scVI** integration (Level 1 §4) and **cell2location**
training (Level 2 §5). Both were run once at full scale and their outputs saved here, so the
notebooks load them instead of training. That is the default — `TRAIN_SCVI = False` and
`TRAIN_C2L = False` in the relevant cells. **No student needs a GPU.**

These files are too large for git, so they are not in the repository. They arrive with the data
bundle:

```bash
bash scripts/fetch_c10_data.sh <bundle-location>
python scripts/check_c10_data.py        # confirms these four, plus the 12 dataset files
```

See [`../data/README.md`](../data/README.md) for the bundle. Nothing needs configuring
afterwards: the notebooks derive `PRECOMP_DIR` from the repository root.

| File | Size | What it is |
|---|---|---|
| `level1_scvi_latent.npz` | 14 MB | scVI 30-dim latent (`X_scvi`, 117,200 × 30) plus matching `obs_names` |
| `level2_c2l_ref_signatures.parquet` | 1.7 MB | cell2location reference signatures (`inf_aver`), 400 epochs |
| `level2_c2l_AT10_mapped.h5ad` | 775 MB | AT10 Visium mapped, 6,000 epochs — abundances in `.obsm["q05_cell_abundance_w_sf"]` |
| `level2_c2l_AT14_mapped.h5ad` | 600 MB | AT14 Visium mapped — same structure |

The two `.h5ad` ship gzipped in the bundle (170 MB and 133 MB); `fetch_c10_data.sh` decompresses
them for you.

## Verify

From the repository root, with the environment active:

```bash
python scratch_build/validate_precomputed.py
```

It loads all four files and checks shapes and alignment on CPU — no GPU, no training.

## Regenerating them

Only needed if you want to reproduce the GPU steps rather than reuse them. Build the CUDA
environment (`bash setup_generic.sh --gpu`), then set `TRAIN_SCVI = True` in Level 1 §4 or
`TRAIN_C2L = True` in Level 2 §5 and run the notebook. Expect hours on a single GPU for the
6,000-epoch cell2location mapping.
