"""CPU-only smoke test for the precomputed GPU-step outputs the students will load.
Mimics exactly what the notebooks' load cells do -- no training, no GPU. Run in the
`single_cell` env on a CPU node/login node."""
import numpy as np, pandas as pd, scanpy as sc, h5py

P = "precomputed"
ok = True

# 1) Level 1 scVI latent -- must reindex onto the reference cell set with no missing cells.
d = np.load(f"{P}/level1_scvi_latent.npz", allow_pickle=True)
lat = pd.DataFrame(d["latent"], index=d["obs_names"].astype(str))
with h5py.File("data/processed/gbm_l1_snrna_AT10_AT14_annotated.h5ad", "r") as f:
    o = f["obs"]; ref_names = o[o.attrs.get("_index", "_index")][:].astype(str)
missing = pd.Index(ref_names).difference(lat.index)
print(f"[L1 scVI]   latent {lat.shape} | reference cells {len(ref_names)} | missing after reindex: {len(missing)}")
ok &= (lat.shape[1] == 30 and len(missing) == 0)

# 2) Level 2 reference signatures.
inf = pd.read_parquet(f"{P}/level2_c2l_ref_signatures.parquet")
print(f"[L2 ref]    inf_aver {inf.shape} (genes x cell types) | e.g. {list(inf.columns)[:2]}")
ok &= (inf.shape[1] >= 10)

# 3) Level 2 mapped sections -- must carry per-spot abundance in obsm.
for tag, n_exp in [("AT10", 3928), ("AT14", 3489)]:
    a = sc.read_h5ad(f"{P}/level2_c2l_{tag}_mapped.h5ad")
    key = "q05_cell_abundance_w_sf"
    has = key in a.obsm
    print(f"[L2 {tag}]   {a.n_obs} spots (expected {n_exp}) | '{key}' present: {has} | abundance shape "
          f"{a.obsm[key].shape if has else 'MISSING'}")
    ok &= (has and a.n_obs == n_exp)

print("\nRESULT:", "ALL PRECOMPUTED FILES LOAD & ALIGN -- students can skip GPU training." if ok
      else "PROBLEM -- see failures above.")
