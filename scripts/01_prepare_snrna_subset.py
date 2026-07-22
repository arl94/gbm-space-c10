"""Build the Level 1 student-facing snRNA-seq dataset (AT10 + AT14, all cells, no
subsampling) plus the instructor-only answer key of stripped ground-truth annotations.

Run inside the `single_cell` conda env:
    conda run -n single_cell python scripts/01_prepare_snrna_subset.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import anndata as ad

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))
from gbmspace_utils.data import split_snrna_answer_key  # noqa: E402

DATA_DIR = PROJECT_ROOT / "data"
# The per-donor source files are an instructor-side input and are NOT part of the released
# data bundle -- only the AT10+AT14 merge this script produces is. See data/README.md.
DONOR_SPLIT_DIR = DATA_DIR / "snRNA_seq/donor_split"
OUT_DIR = DATA_DIR / "snRNA_seq/level1_prepared"
ANSWER_KEY_DIR = DATA_DIR / "answer_keys"

DONORS = ["AT10", "AT14"]


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    ANSWER_KEY_DIR.mkdir(parents=True, exist_ok=True)

    adatas = []
    for donor in DONORS:
        path = DONOR_SPLIT_DIR / f"{donor}.h5ad"
        a = ad.read_h5ad(path)
        print(f"{donor}: {a.n_obs} cells x {a.n_vars} genes  ({path})")
        adatas.append(a)

    combined = ad.concat(adatas, join="inner", index_unique=None)
    combined.obs_names_make_unique()
    print(f"\nCombined (inner join on genes): {combined.n_obs} cells x {combined.n_vars} genes")
    assert combined.n_obs == sum(a.n_obs for a in adatas), "lost cells in concat — investigate"

    # donor_id should already be a per-cell column from the source files; sanity check it
    # rather than trust the concat label, since that's what scripts/notebooks will key on.
    print("donor_id value counts:\n", combined.obs["donor_id"].value_counts())

    student, answer_key = split_snrna_answer_key(combined)

    print(f"\nStudent .obs columns ({len(student.obs.columns)}): {list(student.obs.columns)}")
    print(f"Answer key columns ({len(answer_key.columns)}): {list(answer_key.columns)}")
    assert not (set(answer_key.columns) & set(student.obs.columns)), "answer-key leakage into student obs!"

    student_path = OUT_DIR / "gbm_l1_snrna_AT10_AT14_raw.h5ad"
    answer_key_path = ANSWER_KEY_DIR / "snrna_AT10_AT14_answer_key.parquet"
    student.write_h5ad(student_path)
    answer_key.to_parquet(answer_key_path)

    print(f"\nWrote student file: {student_path}  ({student_path.stat().st_size / 1e9:.2f} GB)")
    print(f"Wrote answer key:   {answer_key_path}  ({answer_key_path.stat().st_size / 1e6:.2f} MB)")
    print(f"\nFinal: {student.n_obs} cells x {student.n_vars} genes")


if __name__ == "__main__":
    main()
