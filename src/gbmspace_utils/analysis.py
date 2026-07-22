"""Shared analysis helpers for the GBM-Space Level 1 (snRNA-seq) and Level 2 (Visium) notebooks.

Marker gene sets below are transcribed from the GBM-Space paper (de Jong, Memi, Gracia,
Lazareva et al., bioRxiv 2025) Methods, Fig. 1C/1D, and Table S5/S6, as summarized by the
paper deep-dive. The same sets are used in both levels: once on single cells (Level 1) and
once on Visium spots (Level 2), to keep the "cell state axis" concept visually consistent
across modalities.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import scanpy as sc
from anndata import AnnData

# The 9 annotation_coarse malignant subclasses, grouped into the paper's 4 major classes.
# Genes are HGNC symbols (matches `var_names` / `var['SYMBOL']` in the provided data).
MALIGNANT_AXIS_MARKERS: dict[str, list[str]] = {
    # --- OPC-NPC-like axis ---
    "OPC-like": ["PDGFRA", "OLIG1", "SOX6"],
    "OPC-NPC-like": ["PDGFRA", "OLIG1", "SOX6", "GRIK2", "DLL3", "GRIA4"],
    "OPC-neuronal-like": ["GRIK2", "DLL3", "GRIA4", "MYT1L", "STMN2"],
    # --- NPC-neuronal-like axis ---
    "NPC-neuronal-like": ["MYT1L", "STMN2", "SOX11", "DCX"],
    # --- AC-gliosis-hypoxia axis (spatial zonation: AC-progenitor -> AC-gliosis -> Gliosis -> Hypoxic) ---
    "AC-progenitor-like": ["SLC1A3", "GFAP", "EGFR", "AQP4", "ALDH1L1"],
    "AC-gliosis-like": ["ITGAV", "ITGB1", "CDH2", "ABCC3"],
    "Gliosis-like": ["JAK2", "STAT3", "ANXA2", "ANXA5", "YAP1", "IFI16", "IL6R", "IL1R1", "SERPINE1", "VEGFA", "AKAP12"],
    "Hypoxic": ["HILPDA", "BNIP3L", "VEGFA", "JUN", "FOS", "HSPA1B"],
    # --- Proliferative (cell-cycle / mitosis program, Table S10 module 7, top genes) ---
    "Proliferative": ["DLGAP5", "CKAP2L", "CDCA2", "CDC25C", "TTK", "BUB1", "HMMR", "CDCA8", "TOP2A", "MKI67", "BIRC5", "CDK1"],
}

# Coarse-subclass -> major-class grouping (the instructor's "4-state axis").
MAJOR_CLASS_OF = {
    "OPC-like": "OPC-NPC-like",
    "OPC-NPC-like": "OPC-NPC-like",
    "OPC-neuronal-like": "OPC-NPC-like",
    "NPC-neuronal-like": "NPC-neuronal-like",
    "AC-progenitor-like": "AC-gliosis-hypoxia",
    "AC-gliosis-like": "AC-gliosis-hypoxia",
    "Gliosis-like": "AC-gliosis-hypoxia",
    "Hypoxic": "AC-gliosis-hypoxia",
    "Proliferative": "Proliferative",
}

# Minimal 4-gene spatial zonation panel (AC-progenitor -> AC-gliosis -> Gliosis -> Hypoxic),
# used by the paper for IHC/Visium validation of the trajectory. Useful even pre-deconvolution.
ZONATION_PANEL = ["AQP4", "ABCC3", "AKAP12", "HILPDA"]

# EMT regulators the paper found "negligible, non-specific" in gliosis/hypoxia states
# (evidence against classical EMT framing of "mesenchymal-like" GBM states).
EMT_MARKERS = ["SNAI1", "SNAI2", "TWIST1", "TWIST2", "ZEB1", "ZEB2"]

# Broad non-malignant TME marker genes (paper Extended Data Fig. 6A; used both as a CNA
# reference-cell selector and for broad cell-type annotation).
TME_MARKERS: dict[str, list[str]] = {
    "Microglia": ["P2RY12", "CX3CR1"],
    "Macrophage/Monocyte": ["CD163", "STAB1", "CD14", "FCGR3A"],
    "Oligodendrocyte": ["MOG", "MOBP", "PLP1", "ST18"],
    "Astrocyte": ["GFAP", "AQP4", "SLC1A3"],
    "Neuron (Exc)": ["SLC17A7", "RBFOX3"],
    "Neuron (Inh)": ["GAD1", "GAD2"],
    "Endothelial": ["CLDN5", "PECAM1", "VWF"],
    "Pericyte": ["PDGFRB", "RGS5"],
    "Lymphocyte": ["CD3E", "CD2", "CD8A", "CD4"],
    "OPC": ["PDGFRA", "OLIG1", "OLIG2"],
}


def score_axis(
    adata: AnnData,
    marker_dict: dict[str, list[str]] | None = None,
    use_raw: bool = True,
    layer: str | None = None,
    min_genes: int = 2,
    verbose: bool = True,
) -> pd.DataFrame:
    """Score every cell/spot against each marker set in `marker_dict` via `sc.tl.score_genes`.

    Mirrors the paper's own method ("a series of gene module scores ... in conjunction
    with the score_genes function in Scanpy"). Returns a DataFrame (cells/spots x states)
    of scores; does NOT write back into `adata.obs` so callers can decide what to keep.
    Categories with fewer than `min_genes` matching genes are skipped (reported if verbose).
    """
    marker_dict = marker_dict or MALIGNANT_AXIS_MARKERS
    var_names = set(adata.raw.var_names) if (use_raw and adata.raw is not None) else set(adata.var_names)

    scores = {}
    for state, genes in marker_dict.items():
        present = [g for g in genes if g in var_names]
        missing = [g for g in genes if g not in var_names]
        if verbose and missing:
            print(f"[score_axis] {state}: missing {missing}, using {present}")
        if len(present) < min_genes:
            print(f"[score_axis] WARNING: skipping '{state}' — only {len(present)} marker(s) found in data")
            continue
        tmp_key = f"_score_tmp_{state}"
        sc.tl.score_genes(adata, gene_list=present, score_name=tmp_key, use_raw=use_raw, layer=layer)
        scores[state] = adata.obs[tmp_key].to_numpy()
        del adata.obs[tmp_key]

    return pd.DataFrame(scores, index=adata.obs_names)


def assign_dominant_state(score_df: pd.DataFrame) -> pd.Series:
    """Assign each cell/spot the column (state) with the highest score. Simple argmax call —
    students should sanity-check this against clustering/marker dotplots rather than trust it blindly,
    exactly as the paper itself treats `score_genes` output as supporting evidence, not a final call.
    """
    return score_df.idxmax(axis=1).astype("category")


def nhood_composition(
    adata: AnnData,
    cell_type_key: str,
    spatial_key: str = "spatial",
    radius: float = 50.0,
) -> pd.DataFrame:
    """Per-spot/cell neighbor composition by type, within `radius` of `spatial_key` coords.
    Requires squidpy. Returns a (cells x cell-types) fraction DataFrame.
    """
    import squidpy as sq

    sq.gr.spatial_neighbors(adata, spatial_key=spatial_key, coord_type="generic", radius=radius)
    onehot = pd.get_dummies(adata.obs[cell_type_key])
    adj = adata.obsp["spatial_connectivities"]
    counts = adj @ onehot.to_numpy()
    counts_df = pd.DataFrame(counts, index=adata.obs_names, columns=onehot.columns)
    totals = counts_df.sum(axis=1).replace(0, np.nan)
    return counts_df.div(totals, axis=0).fillna(0.0)


def spatial_proximity_network(
    adata: AnnData,
    cluster_key: str,
    spatial_key: str = "spatial",
    abundance_df: pd.DataFrame | None = None,
    abundance_threshold: float = 4.0,
    percentile: float = 25.0,
) -> pd.DataFrame:
    """Pairwise spatial-proximity summary between categories in `cluster_key` (or between
    columns of `abundance_df` if given), using a k-d tree of minimum pairwise spot distances
    summarized at `percentile` — this is the paper's own alternative to squidpy's
    nhood_enrichment (their Fig. 2E/3C/6E/7E method), good for a side-by-side comparison.
    Returns a symmetric DataFrame of the `percentile`-th percentile nearest-neighbor distance
    between every pair of categories (smaller = more spatially proximal).
    """
    from scipy.spatial import cKDTree

    coords = adata.obsm[spatial_key]
    if abundance_df is not None:
        categories = abundance_df.columns
        masks = {c: (abundance_df[c] >= abundance_threshold).to_numpy() for c in categories}
    else:
        categories = adata.obs[cluster_key].cat.categories
        masks = {c: (adata.obs[cluster_key] == c).to_numpy() for c in categories}

    result = pd.DataFrame(index=categories, columns=categories, dtype=float)
    for a in categories:
        pts_a = coords[masks[a]]
        if len(pts_a) == 0:
            continue
        tree_a = cKDTree(pts_a)
        for b in categories:
            pts_b = coords[masks[b]]
            if len(pts_b) == 0:
                continue
            dists, _ = tree_a.query(pts_b, k=1)
            result.loc[a, b] = np.percentile(dists, percentile)
    return result
