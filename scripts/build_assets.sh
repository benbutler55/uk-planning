#!/bin/bash
# Build and minify frontend assets using esbuild
set -e

SITE_DIR="$(cd "$(dirname "$0")/.." && pwd)/site"
ASSETS="$SITE_DIR/assets"
DIST="$ASSETS/dist"

# Clean previous build
rm -rf "$DIST"
mkdir -p "$DIST"

echo "Building assets..."

# Minify each JS file individually (no bundling — they're independent IIFEs)
for js in shell.js filters.js tables.js drawers.js; do
  if [ -f "$ASSETS/$js" ]; then
    npx --yes esbuild "$ASSETS/$js" --minify --outfile="$DIST/$js" --log-level=warning
  fi
done

# Minify CSS
npx --yes esbuild "$ASSETS/styles.css" --minify --outfile="$DIST/styles.css" --log-level=warning

# Copy fonts
if [ -d "$ASSETS/fonts" ]; then
  cp -r "$ASSETS/fonts" "$DIST/fonts"
fi

echo ""
echo "Assets built to $DIST/"
echo "---"
ls -lh "$DIST/"
echo "---"
if [ -d "$DIST/fonts" ]; then
  echo "Fonts:"
  ls -lh "$DIST/fonts/"
fi
