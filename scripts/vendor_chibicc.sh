#!/usr/bin/env bash
set -euo pipefail

# Pinned chibicc commit can be updated deliberately after review.
CHIBICC_REPO="https://github.com/rui314/chibicc.git"
CHIBICC_COMMIT="main"
DEST="third_party/chibicc-upstream"

if [ -d "$DEST/.git" ]; then
  echo "chibicc already cloned at $DEST"
else
  git clone "$CHIBICC_REPO" "$DEST"
fi

cd "$DEST"
git fetch --all --tags
if [ "$CHIBICC_COMMIT" != "main" ]; then
  git checkout "$CHIBICC_COMMIT"
else
  git checkout main
fi
git rev-parse HEAD > ../chibicc-upstream-commit.txt

echo "Vendored chibicc commit: $(cat ../chibicc-upstream-commit.txt)"
echo "Preserve $DEST/LICENSE in all derived distributions."
