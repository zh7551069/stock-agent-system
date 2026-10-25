#!/bin/bash
# 把 diagrams/*.d2 渲染成静态 SVG（离线出图，构建/开发前执行）
set -euo pipefail
cd "$(dirname "$0")/.."
D2="${D2:-$(command -v d2 || echo /opt/homebrew/bin/d2)}"
mkdir -p docs/.vuepress/public/diagrams
for f in diagrams/*.d2; do
  name="$(basename "$f" .d2)"
  "$D2" --layout elk --pad 16 --theme 0 "$f" "docs/.vuepress/public/diagrams/$name.svg"
done
echo "d2: rendered $(ls diagrams/*.d2 | wc -l | tr -d ' ') diagrams -> docs/.vuepress/public/diagrams/"
