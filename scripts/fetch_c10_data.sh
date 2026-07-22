#!/usr/bin/env bash
# Fetch the C10 datasets into this repository.
#
#   bash scripts/fetch_c10_data.sh [SOURCE]
#
# SOURCE defaults to the Curnagl staging directory. Pass a local path or a Google Drive
# download instead if you already have the bundle:
#
#   bash scripts/fetch_c10_data.sh ~/Downloads/c10_bundle
#
# The transfer is resumable -- if it drops, re-run the same command and rsync picks up
# where it left off. Afterwards the notebooks find everything with no path edits.
set -eo pipefail

DEFAULT_SOURCE="curnagl:/work/PRTNR/CHUV/DIR/rgottar1/single_cell_all/users/alederer/GBM_Space/c10_bundle/"
SOURCE="${1:-$DEFAULT_SOURCE}"
REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

echo "Source:      $SOURCE"
echo "Destination: $REPO"
echo

# -L dereferences symlinks so the copy is self-contained; --partial makes it resumable.
rsync -avhL --partial --progress \
      --files-from="$REPO/scripts/c10_data_manifest.txt" \
      "$SOURCE" "$REPO/"

echo
echo "Decompressing (.h5ad.gz -> .h5ad; the notebooks read the plain files)..."
find "$REPO/data" "$REPO/precomputed" -name '*.h5ad.gz' -print0 |
    while IFS= read -r -d '' f; do
        out="${f%.gz}"
        [ -f "$out" ] && { echo "  skip (exists): ${out#$REPO/}"; continue; }
        echo "  ${f#$REPO/}"
        gunzip -k "$f"
    done

echo
echo "Done. Verify with:  python scripts/check_c10_data.py"
