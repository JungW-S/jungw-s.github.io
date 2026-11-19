#!/bin/sh
# Build the CV with the bibliography from the homepage's paper records.
set -eu

project_dir=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
output_dir=${1:-"$project_dir/documents"}
mkdir -p "$output_dir"
output_dir=$(CDPATH= cd -- "$output_dir" && pwd)
build_dir=$(mktemp -d "$output_dir/.latex-build.XXXXXXXX")
trap 'rm -rf "$build_dir"' EXIT
trap 'exit 1' HUP INT TERM

python3 "$project_dir/scripts/render-publications.py" "$build_dir"
TEXINPUTS="$build_dir:${TEXINPUTS:-}:"
export TEXINPUTS

cd "$project_dir/documents"
latexmk -pdf -interaction=nonstopmode -halt-on-error -file-line-error \
    -outdir="$build_dir" CV_Woo-SeokJung.tex
mv -f "$build_dir/CV_Woo-SeokJung.pdf" "$output_dir/CV_Woo-SeokJung.pdf"
