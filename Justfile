flags := ""

js:
  ./node_modules/.bin/esbuild \
    --bundle --minify --format=esm  --jsx-factory=h --jsx-fragment=Fragment {{flags}} \
    --out-extension:.js=.min.js \
    --out-extension:.css=.min.css \
    datasette_pins/frontend/targets/**/index.tsx \
    --target=safari12 \
    --outdir=datasette_pins/static

dev:
  DATASETTE_SECRET=abc123 watchexec --signal SIGKILL --restart --clear -e py,ts,js,html,css,sql,yaml -- \
    python3 -m datasette \
      --root \
      --metadata tests/metadata.yaml \
      --config tests/datasette.yaml \
      --internal internal.db \
      legislators.db

test:
  pytest

format:
  black .
