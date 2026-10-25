#!/usr/bin/env bash
# 重新生成 PLAN-02-agent-architecture.html（静态 SVG 内联版，无 JS 依赖）
# 前置：Google Chrome、python3
set -euo pipefail
DIR="$(cd "$(dirname "$0")" && pwd)"
CHROME="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
TMP="$(mktemp -d)"; trap 'rm -rf "$TMP"' EXIT
python3 - "$DIR" "$TMP" <<'PY'
import pathlib, sys
d, tmp = pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2])
tpl = (d/"template.html").read_text(encoding="utf-8")
lib = (d/"mermaid.min.js").read_text(encoding="utf-8")
assert "</script" not in lib.lower()
init = '<script>mermaid.initialize({startOnLoad:true,theme:"base",securityLevel:"loose",' \
       'flowchart:{curve:"basis",htmlLabels:true,padding:14,nodeSpacing:46,rankSpacing:52,useMaxWidth:false},' \
       'themeVariables:{darkMode:true,background:"#121722",primaryColor:"#1a2130",primaryTextColor:"#e6ebf5",' \
       'primaryBorderColor:"#4f8cff",lineColor:"#5a6b86",secondaryColor:"#1a2130",tertiaryColor:"#0f1622",fontSize:"13px"}});</script>'
(tmp/"render.html").write_text(tpl.replace("<!--MERMAID_LIB-->", "<script>\n"+lib+"\n</script>\n"+init), encoding="utf-8")
PY
"$CHROME" --headless=new --disable-gpu --no-sandbox --user-data-dir="$TMP/cr" \
  --window-size=1400,2000 --virtual-time-budget=15000 --dump-dom "file://$TMP/render.html" > "$TMP/dom.html" 2>/dev/null
python3 - "$DIR" "$TMP" <<'PY'
import pathlib, re, sys
d, tmp = pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2])
dom = (tmp/"dom.html").read_text(encoding="utf-8", errors="replace")
body = re.sub(r'<script[\s\S]*?</script>', '', dom, flags=re.I)
svgs = re.findall(r'<svg[\s\S]*?</svg>', body)
tpl = (d/"template.html").read_text(encoding="utf-8")
blocks = re.findall(r'<pre class="mermaid">[\s\S]*?</pre>', tpl)
assert len(svgs) == len(blocks) == 17, f"SVG={len(svgs)} blocks={len(blocks)}"
out = tpl
for b, s in zip(blocks, svgs):
    out = out.replace(b, '<div class="mermaid">\n'+s+'\n</div>', 1)
out = out.replace("<!--MERMAID_LIB-->", "<!-- 图示已预渲染为内联 SVG，无 JS 依赖 -->")
p = d.parent/"PLAN-02-agent-architecture.html"
p.write_text(out, encoding="utf-8")
print(f"生成 {p.name}: {p.stat().st_size:,} B")
PY
