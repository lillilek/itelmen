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
    blocks = []
    esc = html.escape
    for position, para in enumerate(first.findall('paragraphs/paragraph'), 1):
        for seg in para.findall('phrases/*'):
            words = []
            for word in seg.findall('words/word'):
                surface = value(word,'txt') or value(word,'punct')
                morphs = []
                previous = ''
                for morph in word.findall('morphemes/morph'):
                    gloss = value(morph,'gls')
                    lemma = value(morph,'cf')
                    if morph.get('type') in {'root','stem'} and gloss and lemma:
                        roots.setdefault(lemma,gloss)
                    form = value(morph,'txt') or '?'
                    boundary = '=' if previous.endswith('=') or form.startswith('=') else '-'
                    if morphs and not previous.endswith(('-', '=')) and not form.startswith(('-', '=')):
                        form = boundary + form
                    label = (boundary if morphs else '') + (gloss.strip('-=') or '?')
                    morphs.append(f'<span class="m"><span>{esc(form)}</span><small>{esc(label)}</small></span>')
                    previous = form
                if not morphs and not value(word,'punct'):
                    morphs.append('<span class="m"><span>?</span><small>?</small></span>')
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
<style>body{{max-width:66rem;margin:auto;padding:1rem;font:17px/1.5 system-ui;color:#172f4a;background:#edf6ff}}h1,b{{font-family:Georgia,serif}}header,a,summary{{color:#175999}}article,details{{background:white;border:1px solid #c4dcef;border-radius:.5rem;padding:1rem;margin:1rem 0}}.line,.parts{{display:flex}}.line{{flex-wrap:wrap;gap:1rem;align-items:start}}.w,.m{{display:inline-flex;flex-direction:column}}.w{{max-width:100%;overflow:auto}}.m small{{color:#305c85}}p{{margin-bottom:0}}th,td{{text-align:left;padding:.4rem;vertical-align:top}}table{{border-collapse:collapse}}tr{{border-bottom:1px solid #d6e5f3}}input{{font:inherit;padding:.45rem;border:1px solid #7da8cf;border-radius:.35rem;width:min(90%,32rem)}}mark{{background:#a6dcff;color:#102f54;text-decoration:underline;text-underline-offset:.16em}}[hidden]{{display:none}}</style>
<header>Ительменский язык · Корпус</header><h1>{title}</h1><p>Сегментов: {len(blocks)}</p>
<details id="lemmas"><summary>Словарные соответствия для проверки ({len(rows)})</summary><p>Последняя колонка содержит кандидатов с точно совпавшим русским толкованием. Ссылки на словарь требуют подтверждения.</p><table><tr><th>Лемма FLEx</th><th>Глосса основы</th><th>Кандидаты CSV</th></tr>{"".join(rows)}</table></details>
<label>Поиск по словоформам, морфемам, глоссам и переводу<br><input id="q" type="search" placeholder="Например, IPFV"></label> <output id="count" aria-live="polite"></output>
{"".join(blocks)}
<script>{SEARCH}</script></html>'''


SEARCH = r"""
const input = document.querySelector('#q');
const count = document.querySelector('#count');
const records = [...document.querySelectorAll('article')].map(article => {
  const groups = [[...article.querySelectorAll('.w b')], [article.querySelector('p')]];
  for (const word of article.querySelectorAll('.w')) {
    groups.push([...word.querySelectorAll('.m > span')], [...word.querySelectorAll('small')]);
  }
  return {article, groups};
});

function highlight(nodes, separator, query) {
  const parts = nodes.map(node => node.textContent);
  const line = parts.join(separator);
  const pattern = query && new RegExp(query.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'), 'giu');
  const hits = pattern ? [...line.matchAll(pattern)] : [];
  let start = 0;
  nodes.forEach((node, i) => {
    const text = parts[i];
    node.replaceChildren();
    let cursor = 0;
    for (const hit of hits) {
      const left = Math.max(0, hit.index - start);
      const right = Math.min(text.length, hit.index + hit[0].length - start);
      if (right <= left) continue;
      const mark = document.createElement('mark');
      mark.textContent = text.slice(left, right);
      node.append(text.slice(cursor,left), mark);
      cursor = right;
    }
    node.append(text.slice(cursor));
    start += text.length + separator.length;
  });
  return hits.length > 0;
}

function filter() {
  const query = input.value.trim();
  let shown = 0;
  for (const {article,groups} of records) {
    let found = !query;
    groups.forEach((group,i) => {
      if (highlight(group, i === 0 ? ' ' : '', query)) found = true;
    });
    article.hidden = !found;
    if (found) shown++;
  }
  count.textContent = 'Сегментов: ' + shown + ' из ' + records.length;
}
input.addEventListener('input', filter);
filter();
"""


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    for key in ('xml','dictionary','output'): parser.add_argument(key,type=Path)
    args=parser.parse_args()
    args.output.write_text(render(args.xml,args.dictionary),encoding='utf-8')

