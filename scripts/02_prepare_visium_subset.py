"""Build the Level 2 student-facing Visium dataset(s): AT10 (primary) and AT14 (optional
secondary), with the pre-computed cell2location / niche-NMF / IvyGAP-histopathology
"answer key" feature rows stripped out of the gene-expression matrix.

Run inside the `single_cell` conda env:
    conda run -n single_cell python scripts/02_prepare_visium_subset.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import anndata as ad

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))
from gbmspace_utils.data import split_visium_answer_key  # noqa: E402

DATA_DIR = PROJECT_ROOT / "data"
# The full 30-section Visium cohort is an instructor-side input and is NOT part of the
# released data bundle -- only the two prepared sections are. See data/README.md.
VISIUM_SELECTED_DIR = DATA_DIR / "visium/anndata_selected"
OUT_DIR = DATA_DIR / "visium/level2_prepared"
ANSWER_KEY_DIR = DATA_DIR / "answer_keys"

SECTIONS = {
    "primary": "AT10-BRA-5-FO-1_2",
    "secondary_optional": "AT14-BRA-4-FO-2_1",
}


def process_section(role: str, section_name: str) -> None:
    path = VISIUM_SELECTED_DIR / f"{section_name}.h5ad"
    a = ad.read_h5ad(path)
    print(f"\n{role} ({section_name}): {a.n_obs} spots x {a.n_vars} features")
    print("feature_types value counts:\n", a.var["feature_types"].value_counts())

    student, answer_key = split_visium_answer_key(a)
    n_dup = student.var_names.duplicated().sum()
    if n_dup:
        print(f"  {n_dup} duplicate gene symbols (multi-mapped Ensembl IDs) — calling var_names_make_unique()")
        student.var_names_make_unique()
    print(f"  -> student: {student.n_obs} spots x {student.n_vars} genes (Gene Expression only)")
    print(f"  -> answer key: {answer_key.n_obs} spots x {answer_key.n_vars} features")
    assert (student.var["feature_types"] == "Gene Expression").all(), "non-GEX rows leaked into student file!"

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    ANSWER_KEY_DIR.mkdir(parents=True, exist_ok=True)
    student_path = OUT_DIR / f"{section_name}_student.h5ad"
    answer_key_path = ANSWER_KEY_DIR / f"{section_name}_answer_key.h5ad"
    student.write_h5ad(student_path)
    answer_key.write_h5ad(answer_key_path)
    print(f"  wrote {student_path} ({student_path.stat().st_size / 1e6:.1f} MB)")
    print(f"  wrote {answer_key_path} ({answer_key_path.stat().st_size / 1e6:.1f} MB)")


def main() -> None:
    for role, section_name in SECTIONS.items():
        process_section(role, section_name)


if __name__ == "__main__":
    main()
