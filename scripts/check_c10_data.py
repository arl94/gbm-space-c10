"""Verify that the fetched C10 datasets are complete and where the notebooks expect them.

    python scripts/check_c10_data.py

Checks the decompressed files the notebooks actually open, not just the .gz archives.
"""
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]

XENIUM_SAMPLES = {
    "AT410-BRA-5-ORG-E30-MOI0_25-D7-S28-B1": "output-XETG00272__0082677__AT410-BRA-5-ORG-E30-MOI0_25-D7-S28-B1__20260311__143535",
    "AT410-BRA-5-ORG-e25-MOI0_25-D7-S23-B1": "output-XETG00335__0082831__AT410-BRA-5-ORG-e25-MOI0_25-D7-S23-B1__20260311__143630",
    "AT410-BRA-5-ORG-e25-MOI0_25-D14-S73-D2": "output-XETG00155__0097120__AT410-BRA-5-ORG-e25-MOI0_25-D14-S73-D2__20260318__141335",
}

REQUIRED = [
    ("Level 1", "data/snRNA_seq/level1_prepared/gbm_l1_snrna_AT10_AT14_raw.h5ad"),
    ("Level 1", "reference/grch38_gene_positions.parquet"),
    ("Level 1", "precomputed/level1_scvi_latent.npz"),
    ("Level 1b / 2 / 3", "data/processed/gbm_l1_snrna_AT10_AT14_annotated.h5ad"),
    ("Level 2", "data/visium/level2_prepared/AT10-BRA-5-FO-1_2_student.h5ad"),
    ("Level 2", "data/visium/level2_prepared/AT14-BRA-4-FO-2_1_student.h5ad"),
    ("Level 2", "data/answer_keys/AT10-BRA-5-FO-1_2_answer_key.h5ad"),
    ("Level 2", "precomputed/level2_c2l_ref_signatures.parquet"),
    ("Level 2", "precomputed/level2_c2l_AT10_mapped.h5ad"),
    ("Level 2", "precomputed/level2_c2l_AT14_mapped.h5ad"),
]
REQUIRED += [("Level 3", f"data/xenium/{s}_GSO1_annotated.h5ad") for s in XENIUM_SAMPLES]
REQUIRED += [("Level 3 §7-8", f"data/xenium/{d}/transcripts.parquet") for d in XENIUM_SAMPLES.values()]


def human(n):
    for unit in ("B", "KB", "MB", "GB"):
        if n < 1024 or unit == "GB":
            return f"{n:.0f} {unit}" if unit == "B" else f"{n:.1f} {unit}"
        n /= 1024


missing = []
total = 0
width = max(len(p) for _, p in REQUIRED)
for level, rel in REQUIRED:
    path = PROJECT_ROOT / rel
    if path.exists():
        size = path.stat().st_size
        total += size
        print(f"  OK    {rel:<{width}}  {human(size):>9}   [{level}]")
    else:
        gz = path.with_suffix(path.suffix + ".gz")
        hint = "  (found the .gz -- run gunzip on it)" if gz.exists() else ""
        missing.append(rel)
        print(f"  MISS  {rel:<{width}}  {'-':>9}   [{level}]{hint}")

print(f"\n{len(REQUIRED) - len(missing)}/{len(REQUIRED)} present, {human(total)} on disk")
if missing:
    print("\nMissing files -- re-run: bash scripts/fetch_c10_data.sh")
    raise SystemExit(1)
print("All datasets present. The notebooks will find everything.")
