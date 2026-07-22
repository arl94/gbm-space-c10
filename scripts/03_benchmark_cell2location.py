"""Time cell2location's two phases (reference signature NB regression + spatial mapping)
on CPU, at a few epochs, using the *real* chosen AT10+AT14 reference and AT10 Visium
section — then extrapolate to decide FAST (CPU/demo) vs FULL (paper-faithful) epoch
presets for the Level 2 notebook. This is an instructor-side timing probe only: it uses
the answer-key cell-type labels as a stand-in grouping purely to get realistic category
counts/sizes for the reference model — the actual Level 2 notebook will use labels the
students derived themselves in Level 1.

Run inside the `single_cell` conda env, via Slurm (NOT on the login node):
    srun --partition=fast --cpus-per-task=8 --mem=64G --time=02:00:00 \
        conda run -n single_cell python scripts/03_benchmark_cell2location.py
"""

from __future__ import annotations

import time
from pathlib import Path

import anndata as ad
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"

SNRNA_STUDENT = DATA_DIR / "snRNA_seq/level1_prepared/gbm_l1_snrna_AT10_AT14_raw.h5ad"
SNRNA_ANSWER_KEY = DATA_DIR / "answer_keys/snrna_AT10_AT14_answer_key.parquet"
VISIUM_STUDENT = DATA_DIR / "visium/level2_prepared/AT10-BRA-5-FO-1_2_student.h5ad"

REF_PROBE_EPOCHS = 10
MAP_PROBE_EPOCHS = 10
REF_TARGET_PRESETS = {"FAST": 50, "FULL_PAPER": 400}
MAP_TARGET_PRESETS = {"FAST": 500, "FULL_PAPER": 6000}


def time_block(label, fn):
    t0 = time.time()
    result = fn()
    dt = time.time() - t0
    print(f"[TIME] {label}: {dt:.1f}s")
    return result, dt


def main() -> None:
    import scanpy as sc
    import torch
    from cell2location.models import Cell2location, RegressionModel

    print(f"torch num_threads={torch.get_num_threads()}, cuda_available={torch.cuda.is_available()}")

    adata_ref, t_load_ref = time_block("load snRNA reference", lambda: ad.read_h5ad(SNRNA_STUDENT))
    answer_key = pd.read_parquet(SNRNA_ANSWER_KEY)
    adata_ref.obs["cell_type_BENCHMARK_ONLY"] = answer_key.loc[adata_ref.obs_names, "annotation_coarse"].astype("category")
    print(f"Reference: {adata_ref.n_obs} cells, {adata_ref.obs['cell_type_BENCHMARK_ONLY'].nunique()} categories")

    adata_vis, t_load_vis = time_block("load Visium target", lambda: ad.read_h5ad(VISIUM_STUDENT))
    print(f"Visium target: {adata_vis.n_obs} spots, {adata_vis.n_vars} genes")

    shared_genes = sorted(set(adata_ref.var_names) & set(adata_vis.var_names))
    print(f"Shared genes: {len(shared_genes)}")
    adata_ref = adata_ref[:, shared_genes].copy()
    adata_vis = adata_vis[:, shared_genes].copy()

    # Standard cell2location practice: filter to informative genes before training the
    # reference signature model. Training on all 36,601 shared genes measured ~170s/epoch
    # in an earlier run -- this is the fix, not just a smaller epoch count.
    from cell2location.utils.filtering import filter_genes
    selected = filter_genes(adata_ref, cell_count_cutoff=15, cell_percentage_cutoff2=0.05, nonz_mean_cutoff=1.12)
    print(f"Gene filter (cell2location defaults): {len(selected)} / {adata_ref.n_vars} genes kept")
    adata_ref = adata_ref[:, selected].copy()
    adata_vis = adata_vis[:, [g for g in selected if g in adata_vis.var_names]].copy()
    print(f"After filtering: ref {adata_ref.shape}, vis {adata_vis.shape}")

    # --- Phase 1: reference signature (negative binomial regression) ---
    RegressionModel.setup_anndata(adata_ref, batch_key="donor_id", labels_key="cell_type_BENCHMARK_ONLY")
    ref_model = RegressionModel(adata_ref)
    _, t_ref_probe = time_block(
        f"reference model fit, {REF_PROBE_EPOCHS} epochs",
        lambda: ref_model.train(max_epochs=REF_PROBE_EPOCHS, batch_size=10000),
    )
    per_epoch_ref = t_ref_probe / REF_PROBE_EPOCHS
    adata_ref = ref_model.export_posterior(adata_ref, sample_kwargs={"num_samples": 100, "batch_size": 10000})

    # --- Phase 2: spatial mapping ---
    # export_posterior's real varm keys are f"{summary}_per_cluster_mu_fg" for summary in
    # ["means","stds","q05","q95"] (confirmed by reading cell2location's source directly,
    # not the tutorial-quoted "q05_cell_abundance_w_sf" which doesn't actually exist here).
    print(f"varm keys available: {list(adata_ref.varm.keys())}")
    inf_aver = adata_ref.varm["q05_per_cluster_mu_fg"]

    Cell2location.setup_anndata(adata_vis, batch_key="sample_name" if "sample_name" in adata_vis.obs else None)
    sp_model = Cell2location(adata_vis, cell_state_df=inf_aver, N_cells_per_location=30, detection_alpha=200)
    _, t_map_probe = time_block(
        f"spatial mapping fit, {MAP_PROBE_EPOCHS} epochs",
        lambda: sp_model.train(max_epochs=MAP_PROBE_EPOCHS, batch_size=adata_vis.n_obs),
    )
    per_epoch_map = t_map_probe / MAP_PROBE_EPOCHS

    print("\n=== Extrapolated totals (CPU) ===")
    for name, epochs in REF_TARGET_PRESETS.items():
        print(f"Reference [{name}] {epochs} epochs ~= {per_epoch_ref * epochs / 60:.1f} min")
    for name, epochs in MAP_TARGET_PRESETS.items():
        print(f"Mapping   [{name}] {epochs} epochs ~= {per_epoch_map * epochs / 60:.1f} min")
    print("\nUse these numbers to set FAST/FULL epoch defaults in the Level 2 notebook flag.")


if __name__ == "__main__":
    main()
