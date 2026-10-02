"""biz-ideas/*.md → HTML (GitHub Pages: https://csw8929.github.io/sample/biz-ideas/).

Usage: python3 biz-ideas/build.py
"""
import glob
import html
import os
import re
from urllib.parse import quote

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = "csw8929/sample"
ISSUE_NEW = f"https://github.com/{REPO}/issues/new"
MENUS = [
    ("⭐ 평가", "1-rating.yml", "[평가]"),
    ("❓ 상세 질문", "2-question.yml", "[질문]"),
    ("💬 feedback", "3-feedback.yml", "[feedback]"),
]
GRADE_CLASS = {"상": "g-high", "중": "g-mid", "중하": "g-midlow", "하~중": "g-midlow", "하": "g-low"}


def inline(text):
    out = html.escape(text, quote=False)
    out = re.sub(r"\[([^\]]+)\]\(([^)\s]+)\)",
                 lambda m: f'<a href="{html.escape(m.group(2))}" target="_blank" rel="noopener">{m.group(1)}</a>', out)
    out = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", out)
    out = re.sub(r"(?<![*\w])\*([^*]+?)\*(?!\*)", r"<em>\1</em>", out)
    out = re.sub(r"`([^`]+)`", r"<code>\1</code>", out)
    return out


def render_table(rows):
    cells = [[c.strip() for c in row.strip().strip("|").split("|")] for row in rows]
    head, body = cells[0], [r for r in cells[2:]]
    parts = ['<div class="table-wrap"><table><thead><tr>']
    parts += [f"<th>{inline(c)}</th>" for c in head]
    parts.append("</tr></thead><tbody>")
    for row in body:
        parts.append("<tr>" + "".join(f"<td>{inline(c)}</td>" for c in row) + "</tr>")
    parts.append("</tbody></table></div>")
    return "".join(parts)


def render_blocks(text):
    lines = text.strip("\n").split("\n")
    out, index = [], 0
    while index < len(lines):
        line = lines[index]
        if not line.strip():
            index += 1
        elif line.startswith("|"):
            rows = []
            while index < len(lines) and lines[index].startswith("|"):
                rows.append(lines[index])
                index += 1
            out.append(render_table(rows))
        elif re.match(r"^\s*- ", line):
            out.append(render_list(lines, index))
            while index < len(lines) and (re.match(r"^\s*- ", lines[index]) or lines[index].startswith("  ")):
                index += 1
        elif line.startswith("### "):
            out.append(f"<h4>{inline(line[4:])}</h4>")
            index += 1
        elif line.startswith("## "):
            out.append(f"<h3>{inline(line[3:])}</h3>")
            index += 1
        else:
            para = []
            while index < len(lines) and lines[index].strip() and not lines[index].startswith(("|", "- ", "#")):
                para.append(lines[index])
                index += 1
            out.append(f"<p>{inline(' '.join(para))}</p>")
    return "\n".join(out)


def render_list(lines, start):
    out, stack, index = [], [], start
    while index < len(lines):
        match = re.match(r"^(\s*)- (.*)$", lines[index])
        if not match:
            if lines[index].startswith("  ") and out:
                out[-1] = out[-1][:-5] + " " + inline(lines[index].strip()) + "</li>"
                index += 1
                continue
            break
        depth = len(match.group(1)) // 2
        while len(stack) < depth + 1:
            out.append("<ul>")
            stack.append(depth)
        while len(stack) > depth + 1:
            out.append("</ul>")
            stack.pop()
        out.append(f"<li>{inline(match.group(2))}</li>")
        index += 1
    out.extend("</ul>" for _ in stack)
    return "".join(out)


def text_width(label):
    return sum(15 if ord(ch) > 0x2E80 else 8 for ch in label) + 28


def render_flow(spec):
    groups = {}
    for raw in spec.strip().split("\n"):
        match = re.match(r"^(\S+):\s*(.+?)\s+(-x->|-->)\s+(.+?)\s*:\s*(.+)$", raw.strip())
        if not match:
            continue
        group, source, arrow, target, label = match.groups()
        groups.setdefault(group, []).append((source, target, arrow == "-x->", label))
    row_height, gap, left = 92, 70, 64
    rows_svg, max_x = [], 0
    for row, (group, edges) in enumerate(groups.items()):
        y = 22 + row * row_height
        nodes = []
        for source, target, _, _ in edges:
            for node in (source, target):
                if node not in nodes:
                    nodes.append(node)
        x, boxes = left, {}
        for node in nodes:
            width = text_width(node)
            boxes[node] = (x, width)
            x += width + gap
        max_x = max(max_x, x - gap)
        tone = "bad" if group == "원래" else "good"
        rows_svg.append(f'<text class="f-group {tone}" x="0" y="{y + 26}">{html.escape(group)}</text>')
        for node, (bx, width) in boxes.items():
            rows_svg.append(f'<rect class="f-box {tone}" x="{bx}" y="{y + 6}" width="{width}" height="32" rx="8"/>'
                            f'<text class="f-node" x="{bx + width / 2}" y="{y + 27}" text-anchor="middle">{html.escape(node)}</text>')
        for source, target, blocked, label in edges:
            sx, sw = boxes[source]
            tx, _ = boxes[target]
            x1, x2, ay = sx + sw + 4, tx - 6, y + 22
            cls = "f-arrow blocked" if blocked else "f-arrow"
            marker = "url(#ah-bad)" if blocked else "url(#ah)"
            rows_svg.append(f'<line class="{cls}" x1="{x1}" y1="{ay}" x2="{x2}" y2="{ay}" marker-end="{marker}"/>')
            mid = (x1 + x2) / 2
            rows_svg.append(f'<text class="f-label" x="{mid}" y="{y + 62}" text-anchor="middle">{html.escape(label)}</text>')
            if blocked:
                rows_svg.append(f'<text class="f-x" x="{mid}" y="{ay + 6}" text-anchor="middle">✕</text>')
    height = 22 + len(groups) * row_height
    defs = ('<defs><marker id="ah" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto">'
            '<path d="M0,0 L10,5 L0,10 z" class="f-head"/></marker>'
            '<marker id="ah-bad" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto">'
            '<path d="M0,0 L10,5 L0,10 z" class="f-head bad"/></marker></defs>')
    return (f'<figure class="flow"><svg width="{max_x + 10}" height="{height}" viewBox="0 0 {max_x + 10} {height}" role="img" aria-label="돈의 흐름">'
            f'{defs}{"".join(rows_svg)}</svg>'
            '<figcaption>빨간 ✕ = 원래 모양에서 돈이 안 흐르는 곳 · 초록 = 살리는 변형에서 돈이 흐르는 길</figcaption></figure>')


def menu_buttons(number, name):
    buttons = []
    for label, template, prefix in MENUS:
        title = quote(f"{prefix} #{number} {name}")
        url = f"{ISSUE_NEW}?template={template}&title={title}&idea={quote('#' + number)}"
        buttons.append(f'<a class="act" href="{url}" target="_blank" rel="noopener">{label}</a>')
    return "".join(buttons)


def parse_idea(section):
    head = re.search(r"^## #(\d{3}) (.+)$", section, flags=re.M)
    number, name = head.group(1), head.group(2).strip()
    by_codex = "(Codex)" in name
    clean_name = re.sub(r"\s*\*\(Codex\)\*", "", name)
    body = section[head.end():]
    body = re.sub(r"^\*\*메뉴\*\*.*$", "", body, flags=re.M)

    def cut(text, start_marker, end_markers):
        start = text.find(start_marker)
        if start < 0:
            return ""
        start += len(start_marker)
        ends = [text.find(marker, start) for marker in end_markers]
        ends = [e for e in ends if e >= 0]
        return text[start:min(ends) if ends else len(text)]

    overview = body[:min(i for i in [body.find("### 🔍"), body.find("<details>"), len(body)] if i >= 0)]
    verdict_head = re.search(r"### 🔍 검증 결과 — 사업 가능성: \*\*(.+?)\*\*", body)
    grade = verdict_head.group(1) if verdict_head else "?"
    verdict = cut(body, verdict_head.group(0), ["<details>", "### 🖼", "### 반응"]) if verdict_head else ""
    easy = cut(body, "</summary>", ["</details>"])
    flow = cut(body, "```flow\n", ["```"])
    reaction = cut(body, "### 반응", ["\n---"])
    return dict(number=number, name=clean_name, codex=by_codex, grade=grade,
                overview=overview, verdict=verdict, easy=easy, flow=flow, reaction=reaction)


def render_idea(idea):
    number = idea["number"]
    grade_cls = GRADE_CLASS.get(idea["grade"], "g-mid")
    codex = '<span class="tag">Codex</span>' if idea["codex"] else ""
    tabs = [("overview", "개요", render_blocks(idea["overview"])),
            ("verdict", "🔍 검증", render_blocks(idea["verdict"])),
            ("easy", "💡 쉽게 설명", render_blocks(idea["easy"]))]
    if idea["flow"]:
        tabs.append(("flow", "🖼 돈의 흐름", render_flow(idea["flow"])))
    tab_buttons = "".join(
        f'<button class="tab{" on" if i == 0 else ""}" data-panel="p{number}-{key}">{label}</button>'
        for i, (key, label, _) in enumerate(tabs))
    panels = "".join(
        f'<div class="panel{" on" if i == 0 else ""}" id="p{number}-{key}">{content}</div>'
        for i, (key, _, content) in enumerate(tabs))
    return f"""
<article class="idea" id="i{number}">
  <header>
    <span class="num">#{number}</span>
    <h2>{html.escape(idea['name'])}</h2>
    <span class="grade {grade_cls}">가능성 {html.escape(idea['grade'])}</span>{codex}
  </header>
  <nav class="tabs">{tab_buttons}</nav>
  {panels}
  <div class="actions">{menu_buttons(number, idea['name'])}</div>
  <section class="reactions" data-idea="#{number}">
    <h4>반응</h4>
    <div class="static">{render_blocks(idea['reaction']) or ''}</div>
    <ul class="live"></ul>
  </section>
</article>"""


CSS = """
:root{--bg:#f7f7f5;--card:#fff;--ink:#1d1d1f;--sub:#5f6368;--line:#e3e3e0;--accent:#2563eb;
--high:#15803d;--mid:#ca8a04;--midlow:#ea580c;--low:#dc2626;--good:#16a34a;--bad:#dc2626;--chip:#eef2ff}
@media (prefers-color-scheme:dark){:root:not([data-theme=light]){--bg:#111214;--card:#1b1c1f;--ink:#ececec;
--sub:#a0a4ab;--line:#2c2e33;--accent:#7aa2ff;--chip:#1f2638}}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);
font:16px/1.65 -apple-system,BlinkMacSystemFont,"Apple SD Gothic Neo","Noto Sans KR","Malgun Gothic",sans-serif}
main{max-width:920px;margin:0 auto;padding:24px 16px 64px}
a{color:var(--accent)}h1{font-size:1.5rem;margin:.2em 0}.sub{color:var(--sub)}
.idea,.summary{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:18px 18px 14px;margin:18px 0}
.idea header{display:flex;flex-wrap:wrap;align-items:center;gap:8px 10px}
.idea h2{font-size:1.18rem;margin:0;flex:1 1 260px}.num{color:var(--sub);font-weight:600}
.grade{font-size:.85rem;font-weight:700;color:#fff;border-radius:999px;padding:2px 10px}
.g-high{background:var(--high)}.g-mid{background:var(--mid)}.g-midlow{background:var(--midlow)}.g-low{background:var(--low)}
.tag{font-size:.75rem;border:1px solid var(--line);border-radius:6px;padding:1px 6px;color:var(--sub)}
.tabs{display:flex;flex-wrap:wrap;gap:6px;margin:14px 0 6px;border-bottom:1px solid var(--line)}
.tab{border:0;background:none;color:var(--sub);font:inherit;font-size:.93rem;padding:6px 10px;cursor:pointer;border-bottom:2px solid transparent}
.tab.on{color:var(--ink);border-bottom-color:var(--accent);font-weight:600}
.panel{display:none;padding-top:6px}.panel.on{display:block}
.panel ul{padding-left:1.2em}.panel li{margin:.3em 0}
.actions{display:flex;flex-wrap:wrap;gap:8px;margin-top:12px}
.act{text-decoration:none;border:1px solid var(--line);border-radius:10px;padding:7px 12px;background:var(--chip);color:var(--ink);font-size:.93rem}
.act:hover{border-color:var(--accent)}
.reactions{margin-top:12px;border-top:1px dashed var(--line);padding-top:6px}
.reactions h4{margin:.3em 0;font-size:.95rem;color:var(--sub)}.reactions .live{padding-left:1.1em;margin:0}
.table-wrap{overflow-x:auto}table{border-collapse:collapse;width:100%;font-size:.93rem}
th,td{border-bottom:1px solid var(--line);padding:6px 8px;text-align:left;vertical-align:top}
.flow{margin:6px 0}.flow svg{max-width:100%;height:auto}
.flow figcaption{font-size:.85rem;color:var(--sub)}
.f-box{fill:var(--card);stroke-width:1.6}.f-box.good{stroke:var(--good)}.f-box.bad{stroke:var(--bad)}
.f-node{fill:var(--ink);font-size:14px}.f-label{fill:var(--sub);font-size:12.5px}
.f-group{font-size:14px;font-weight:700}.f-group.good{fill:var(--good)}.f-group.bad{fill:var(--bad)}
.f-arrow{stroke:var(--good);stroke-width:2}.f-arrow.blocked{stroke:var(--bad);stroke-dasharray:5 4}
.f-head{fill:var(--good)}.f-head.bad{fill:var(--bad)}.f-x{fill:var(--bad);font-size:16px;font-weight:700}
code{background:var(--chip);border-radius:4px;padding:0 4px}
"""

JS = """
document.querySelectorAll('.idea').forEach(card=>{
  card.querySelectorAll('.tab').forEach(tab=>tab.addEventListener('click',()=>{
    card.querySelectorAll('.tab,.panel').forEach(el=>el.classList.remove('on'));
    tab.classList.add('on');document.getElementById(tab.dataset.panel).classList.add('on');
  }));
});
fetch('https://api.github.com/repos/REPO/issues?state=all&per_page=100').then(r=>r.ok?r.json():[]).then(issues=>{
  document.querySelectorAll('.reactions').forEach(box=>{
    const tag=box.dataset.idea;
    const mine=issues.filter(i=>(i.title+' '+(i.body||'')).includes(tag));
    const ul=box.querySelector('.live');
    mine.forEach(i=>{const li=document.createElement('li');const a=document.createElement('a');
      a.href=i.html_url;a.target='_blank';a.textContent=i.title+(i.comments?` (답글 ${i.comments})`:'');
      li.appendChild(a);ul.appendChild(li);});
  });
}).catch(()=>{});
""".replace("REPO", REPO)


def page(title, body, back=True):
    nav = '<p><a href="index.html">← 전체 목록</a> · <a href="https://github.com/' + REPO + '/issues" target="_blank">이슈(반응) 전체</a></p>' if back else ""
    return f"""<!doctype html><html lang="ko"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>{html.escape(title)}</title>
<style>{CSS}</style></head><body><main>{nav}{body}</main><script>{JS}</script></body></html>"""


def build_day(path):
    text = open(path, encoding="utf-8").read()
    title = re.search(r"^# (.+)$", text, flags=re.M).group(1)
    sections = re.split(r"\n---\n", text)
    head = re.sub(r"^# .+$", "", sections[0], flags=re.M)
    head = re.sub(r"^\[← 목록\].*$", "", head, flags=re.M)
    ideas = [parse_idea(s) for s in sections[1:] if re.search(r"^## #\d{3} ", s, flags=re.M)]
    body = f"<h1>{inline(title)}</h1>"
    body += f'<section class="summary">{render_blocks(head)}</section>'
    body += "".join(render_idea(idea) for idea in ideas)
    out = os.path.splitext(path)[0] + ".html"
    open(out, "w", encoding="utf-8").write(page(title, body))
    return title, os.path.basename(out), ideas


def main():
    days = sorted(glob.glob(os.path.join(HERE, "20[0-9][0-9][01][0-9][0-3][0-9].md")), reverse=True)
    rows = []
    for path in days:
        title, href, ideas = build_day(path)
        rows.append(f'<section class="summary"><h3><a href="{href}">{inline(title)}</a></h3><ul>' + "".join(
            f'<li><a href="{href}#i{i["number"]}">#{i["number"]} {html.escape(i["name"])}</a> '
            f'<span class="grade {GRADE_CLASS.get(i["grade"], "g-mid")}">{html.escape(i["grade"])}</span></li>'
            for i in ideas) + "</ul></section>")
    intro = ("<h1>사업 아이디어 — 하루 5개</h1>"
             '<p class="sub">2026-10-02 ~ 10-08 일주일 시범 · 10-09 에 함께 돌아본다. '
             "아이디어마다 ⭐ 평가 · ❓ 상세 질문 · 💬 feedback 을 누르면 양식이 열리고, Claude 가 감지해 반응한다. "
             "💡 쉽게 설명과 🖼 돈의 흐름은 탭에서 본다.</p>")
    open(os.path.join(HERE, "index.html"), "w", encoding="utf-8").write(page("사업 아이디어", intro + "".join(rows), back=False))
    print("built", len(days), "days")


if __name__ == "__main__":
    main()
