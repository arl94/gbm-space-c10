#!/usr/bin/env bash
# Fetch the C10 datasets into this repository.
#
#   bash scripts/fetch_c10_data.sh [SOURCE]
#
# SOURCE is where the C10 data bundle lives. Usually a folder you downloaded and unpacked:
#
#   bash scripts/fetch_c10_data.sh ~/Downloads/c10_bundle
#
# See data/README.md for where to get the bundle. Instructors on Curnagl can pass the staging
# path directly:  bash scripts/fetch_c10_data.sh curnagl:/work/.../GBM_Space/c10_bundle/
#
# The transfer is resumable -- if it drops, re-run the same command and rsync picks up
# where it left off. Afterwards the notebooks find everything with no path edits.
set -eo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

if [ -z "${1:-}" ]; then
    cat >&2 <<USAGE
Usage: bash scripts/fetch_c10_data.sh <bundle-location>

  <bundle-location> is the C10 data bundle: a local folder you downloaded and
  unpacked, or any rsync-reachable path.

    bash scripts/fetch_c10_data.sh ~/Downloads/c10_bundle
    bash scripts/fetch_c10_data.sh user@host:/path/to/c10_bundle

  See data/README.md for where to obtain the bundle (5.1 GB, decompresses to
  11.7 GB) and what it contains.
USAGE
    exit 2
fi
SOURCE="$1"

case "$SOURCE" in
    *:*) ;;                                    # remote -- let rsync/ssh resolve it
    *) [ -d "$SOURCE" ] || { echo "ERROR: no such directory: $SOURCE" >&2; exit 1; } ;;
esac
# rsync needs the trailing slash to copy the contents rather than the folder itself.
case "$SOURCE" in */) ;; *) SOURCE="$SOURCE/" ;; esac

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
