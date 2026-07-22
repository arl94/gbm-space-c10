# C10 datasets

The datasets are distributed separately from the code — they are far too large for git.
Fetch them with:

```bash
bash scripts/fetch_c10_data.sh                 # from the cluster
bash scripts/fetch_c10_data.sh ~/Downloads/c10_bundle   # from a Google Drive download
python scripts/check_c10_data.py               # confirm everything landed
```

The exact file list lives in [`scripts/c10_data_manifest.txt`](../scripts/c10_data_manifest.txt)
and contains only files a notebook actually opens. The fetch script decompresses the
`.h5ad.gz` archives afterwards, because the notebooks read the plain `.h5ad`.

Sizes below are **on disk after decompression** and total 15.4 GB. The transfer itself is
**5.1 GB** — the large `.h5ad` files ship gzipped and compress 3–4× (the cell2location maps go
812 MB → 178 MB, the annotated reference 2.8 GB → 830 MB).

## What each file is, and who reads it

| File | Size | Read by |
|---|---|---|
| `snRNA_seq/level1_prepared/gbm_l1_snrna_AT10_AT14_raw.h5ad` | 3.9 GB | **Level 1** — the starting point. 118,471 nuclei × ~36k genes, donors AT10 + AT14, raw integer counts in `.X`, no annotation. |
| `../reference/grch38_gene_positions.parquet` | 1 MB | **Level 1** §7 — GRCh38 gene coordinates that inferCNV needs to walk the genome. |
| `../precomputed/level1_scvi_latent.npz` | 14 MB | **Level 1** §4 — the GPU-trained scVI latent (117,200 × 30) plus matching `obs_names`, so the integration step works without a GPU. |
| `processed/gbm_l1_snrna_AT10_AT14_annotated.h5ad` | 6.3 GB | **Level 1 output**, then the input to **Levels 1b, 2 and 3**. Carries `cell_type`, `cell_status_derived`, `malignant_state`, `malignant_class`, raw counts in `.layers["counts"]`. |
| `visium/level2_prepared/AT10-BRA-5-FO-1_2_student.h5ad` | 271 MB | **Level 2** — the primary Visium section, answer-key feature rows stripped out. |
| `visium/level2_prepared/AT14-BRA-4-FO-2_1_student.h5ad` | 209 MB | **Level 2** §10 and **Level 3** — the second tumor, for the cross-tumor check. |
| `answer_keys/AT10-BRA-5-FO-1_2_answer_key.h5ad` | 18 MB | **Level 2** §9 — the paper's own niche and cell-state abundances for that section, in `.var["feature_types"]` blocks. |
| `answer_keys/AT14-BRA-4-FO-2_1_answer_key.h5ad` | 15 MB | Not used by a notebook; kept so the AT14 comparison can be scored too. |
| `answer_keys/snrna_AT10_AT14_answer_key.parquet` | 4 MB | `scripts/03_benchmark_cell2location.py` only. The Level 1 ground-truth labels. |
| `../precomputed/level2_c2l_ref_signatures.parquet` | 2 MB | **Level 2** §5 — the cell2location reference signature (400 epochs, GPU). |
| `../precomputed/level2_c2l_{AT10,AT14}_mapped.h5ad` | 775 + 600 MB | **Level 2** §5 — the finished 6,000-epoch cell2location mapping for each section, so the deconvolution runs on CPU in seconds. |
| `xenium/AT410-*_GSO1_annotated.h5ad` (×3) | 828 MB | **Level 3** — the three organoid sections as cell-by-gene AnnData, 5,101-gene panel, already annotated. |
| `xenium/output-XETG*/transcripts.parquet` (×3) | 2.5 GB | **Level 3** §7–8 only — the per-molecule transcript table, for the nuclear-vs-cytoplasmic analysis. |
| `paper/GBM-Space-*.pdf`, `-media-3.xlsx` | 45 MB | The source paper and supplements. Withheld from students until the Level 2 reveal; read in **Level 1b**. |

The paper is de Jong, Memi, Gracia, Lazareva et al., bioRxiv 2025.05.13.653495
([gbmspace.org](https://www.gbmspace.org/)).

## What is deliberately not included

| Left out | Why |
|---|---|
| The rest of each `output-XETG*/` folder (~40 GB) | `morphology.ome.tif`, the zarr stores, cell/nucleus boundaries and the analysis folder. Only `transcripts.parquet` is ever read. Needed only for the unreleased Level 3 BASIS segmentation notebook. |
| `visium/anndata_selected/` (3.9 GB) | The full 30-section Visium cohort. Only the two prepared sections are used; `scripts/02_prepare_visium_subset.py` records how they were derived. |
| `snRNA_seq/donor_split/` (1.1 GB) | The per-donor snRNA files that `scripts/01_prepare_snrna_subset.py` merges into the Level 1 input. |
| `*.tar.gz` archives | Redundant packed copies of the above. |

If you need any of these, they remain on Curnagl under
`/work/PRTNR/CHUV/DIR/rgottar1/single_cell_all/users/alederer/{C10,GBM_Space}/`.
