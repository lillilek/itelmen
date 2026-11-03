"""Build a self-contained, local review of one FLEx text and dictionary candidates."""
import argparse
import csv
import html
from pathlib import Path
import re
import xml.etree.ElementTree as ET


def value(node, kind):
    return next((i.text.strip() for i in node.findall('item')
                 if i.get('type') == kind and i.text and i.text.strip()), '')


def render(xml, dictionary):
    texts = ET.parse(xml).getroot().findall('interlinear-text')
    first = texts[0]
    with dictionary.open(encoding='utf-8-sig', newline='') as stream:
        entries = list(csv.DictReader(stream))
    roots = {}
    labels = set()
    blocks = []
    esc = html.escape
    for position, para in enumerate(first.findall('paragraphs/paragraph'), 1):
        for seg in para.findall('phrases/*'):
            words = []
            for word in seg.findall('words/word'):
                surface = value(word,'txt') or value(word,'punct')
                morphs = []
                for morph in word.findall('morphemes/morph'):
                    gloss = value(morph,'gls')
                    lemma = value(morph,'cf')
                    if morph.get('type') in {'root','stem'} and gloss and lemma:
                        roots.setdefault(lemma,gloss)
                    if re.fullmatch(r'[A-Z0-9][A-Z0-9.():_-]*',gloss):
                        labels.add(gloss)
                    morphs.append(f'<span class="m"><span>{esc(value(morph,"txt"))}</span><small>{esc(gloss) or "·"}</small></span>')
                words.append(f'<span class="w"><b>{esc(surface)}</b><span class="parts">{"".join(morphs)}</span></span>')
            n = len(blocks)+1
            blocks.append(f'<article id="s{n}" data-p="{position}"><a href="#s{n}">§ {n}</a><div class="line">{"".join(words)}</div><p>{esc(value(seg,"gls"))}</p></article>')
    rows = []
    for lemma, gloss in roots.items():
        if not re.search('[а-яА-ЯёЁ]',gloss): continue
        candidates = [e['слово'] for e in entries if e['толкование'].strip().casefold()==gloss.casefold()]
        rows.append(f'<tr><td>{esc(lemma)}</td><td>{esc(gloss)}</td><td>{esc(", ".join(candidates)) or "—"}</td></tr>')
        if len(rows)==15: break
    title=esc(value(first,'title'))
    return f'''<!doctype html><html lang="ru"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{title} · Ительменский корпус</title>
<style>body{{max-width:66rem;margin:auto;padding:1rem;font:17px/1.5 system-ui;color:#182e2d;background:#faf9f5}}h1,b{{font-family:Georgia,serif}}article,details{{background:white;border:1px solid #d9e2dd;border-radius:.5rem;padding:1rem;margin:1rem 0}}.line,.parts{{display:flex}}.line{{flex-wrap:wrap;gap:1rem;align-items:start}}.w,.m{{display:inline-flex;flex-direction:column}}.w{{max-width:100%;overflow:auto}}.m small{{color:#34645c}}.m+ .m{{margin-left:.08em}}p{{margin-bottom:0}}a{{color:#325c50}}th,td{{text-align:left;padding:.4rem;vertical-align:top}}table{{border-collapse:collapse}}tr{{border-bottom:1px solid #ddd}}input{{font:inherit;width:min(96%,32rem)}}[hidden]{{display:none}}</style>
<header>Ительменский язык · Корпус</header><h1>{title}</h1><p>Пилот для сверки · {len(blocks)} сегментов · {len(texts)} текстов в исходном XML</p>
<details id="lemmas"><summary>Словарные соответствия для проверки ({len(rows)})</summary><p>Последняя колонка содержит кандидатов с точно совпавшим русским толкованием. Ссылки на словарь требуют подтверждения.</p><table><tr><th>Лемма FLEx</th><th>Глосса основы</th><th>Кандидаты CSV</th></tr>{"".join(rows)}</table></details>
<details><summary>Метки в этом тексте</summary>{esc(" · ".join(sorted(labels)))}</details>
<label>Найти в тексте, глоссах или переводе<br><input id="q" type="search"></label><output id="count"></output>
{"".join(blocks)}
<script>const articles=[...document.querySelectorAll('article')];function filter(){{const query=q.value.normalize().toLowerCase();let n=0;for(const a of articles){{a.hidden=!a.textContent.normalize().toLowerCase().includes(query);if(!a.hidden)n++}}count.textContent=' '+n+' / '+articles.length}}q.oninput=filter;filter()</script></html>'''


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    for key in ('xml','dictionary','output'): parser.add_argument(key,type=Path)
    args=parser.parse_args()
    args.output.write_text(render(args.xml,args.dictionary),encoding='utf-8')

