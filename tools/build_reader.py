"""Build the static corpus reader from FLEx exports, the dictionary and spelling rules."""
from pathlib import Path
import json, csv, re, argparse, unicodedata
from collections import defaultdict
import xml.etree.ElementTree as ET
from build_pilot import value


def transliterate(text,rules):
    text=unicodedata.normalize('NFC',text.lower())
    result=''
    i=0
    while i<len(text):
        ch=text[i]
        if ch in 'яёю':
            result+=('j' if i==0 or text[i-1] in 'аеёиоуыэюяәӑ' else 'ʲ')+dict(я='a',ё='o',ю='u')[ch]
            i+=1
            continue
        key=next((k for k in rules if text.startswith(k,i)),None)
        if key:
            result+=rules[key]
            i+=len(key)
        elif 'CYRILLIC' in unicodedata.name(ch,''):
            return ''
        else:
            result+=ch
            i+=1
    return result


POS={'n':'существительное','v':'глагол','adv':'наречие','adj':'прилагательное','pro':'местоимение','interj':'междометие','num':'числительное','conj':'союз','ptcl':'частица','coordconn':'союз','subordconn':'союз','cardnum':'числительное','ordnum':'числительное','pers':'местоимение','relpro':'местоимение'}
FORM_FIELDS=('слово','фонетический вариант','северный диалектный вариант','инфинитив','множественное число','общее число')

def norm(s):
    return unicodedata.normalize('NFC',s.strip()).casefold().translate(str.maketrans({"’":"ʼ","'":"ʼ","ʹ":"ʼ"}))

def build(xmls, dictionary, rule_file, output):
    rules=dict(sorted(json.loads(rule_file.read_text(encoding='utf8')).items(),key=lambda kv:-len(kv[0])))
    idx=defaultdict(set)
    with dictionary.open(encoding='utf-8-sig',newline='') as f:
        for row in csv.DictReader(f):
            for col in FORM_FIELDS:
                for variant in re.split('[;,]',row.get(col+' (латиница)','') or transliterate(row.get(col,''),rules)):
                    if not variant.strip(): continue
                    for gloss in re.split('[,;]',row['толкование']):
                        if gloss.strip(): idx[norm(variant),norm(row['часть речи']),norm(gloss)].add(row['id статьи'])
    witnesses=defaultdict(set)
    pending=[]
    ids=set()
    segments=[]
    for xml in xmls:
        for t in ET.parse(xml).getroot().findall('interlinear-text'):
            guid=t.attrib['guid']
            if guid in ids: raise ValueError('Повтор GUID '+guid)
            ids.add(guid)
            title=next((i.text.strip() for i in t.findall("item[@type='title'][@lang='itl']") if i.text and i.text.strip()),'')
            if not title: raise ValueError('Нет ительменского названия: '+guid)
            title=re.sub(r'^\s*\d+\s*[.)]\s*','',title)
            for p,para in enumerate(t.findall('paragraphs/paragraph'),1):
                for seg in para.findall('phrases/*'):
                    num=value(seg,'segnum')
                    words=[]
                    for w in seg.findall('words/word'):
                        parts=[]
                        previous=''
                        mono=sum(m.get('type') in ('root','stem') for m in w.findall('morphemes/morph'))==1
                        for m in w.findall('morphemes/morph'):
                            form=value(m,'txt') or '?'
                            boundary='=' if previous.endswith('=') or form.startswith('=') else '-'
                            gloss=value(m,'gls')
                            lemma=value(m,'cf')
                            entry=''
                            if parts and not previous.endswith(('-','=')) and not form.startswith(('-','=')): form=boundary+form
                            parts.append([form,(boundary if parts else '')+(gloss.strip('-=') or '?'),lemma,entry])
                            if m.get('type') in ('root','stem') and lemma and gloss:
                                cat=POS.get(value(m,'msa')) or POS.get(value(w,'pos'))
                                key=(norm(lemma),cat,norm(gloss))
                                witnesses[key].update(idx.get(key,()))
                                if mono:
                                    witnesses[key].update(idx.get((norm(value(w,'txt')),cat,norm(gloss)),()))
                                pending.append((parts[-1],key))
                            previous=form
                        if not parts and not value(w,'punct'):parts=[['?','?','','']]
                        words.append([value(w,'txt') or value(w,'punct'),value(w,'pos'),parts])
                    if not words or not num:raise ValueError('Пустой сегмент '+guid)
                    segments.append(dict(id=guid+'-'+num,t=title,p=p,n=num,w=words,r=value(seg,'gls')))
    for part,key in pending:
        if len(witnesses[key])==1: part[3]=next(iter(witnesses[key]))
    if len({s['id'] for s in segments})!=len(segments):raise ValueError('Повтор ID сегмента')
    payload=json.dumps(segments,ensure_ascii=False,separators=(',',':')).replace('<','\\u003c')
    page=Path(__file__).with_name('reader.html').read_text(encoding='utf8').replace('CORPUS_PAYLOAD',payload)
    output.write_text(page,encoding='utf8')
    counts=defaultdict(int)
    for seg in segments:
        for entry in {m[3] for w in seg['w'] for m in w[2] if m[3]}:
            counts[entry]+=1
    (output.parent/'data').mkdir(exist_ok=True)
    (output.parent/'data/examples.json').write_text(json.dumps(counts),encoding='utf8')
    tags=sorted({m[1].lstrip('-=') for s in segments for w in s['w'] for m in w[2] if re.match('[A-Z0-9]',m[1].lstrip('-='))})
    glossary=output.parent/'data/glossary.csv'
    descriptions={}
    if glossary.exists():
        with glossary.open(encoding='utf-8-sig',newline='') as f:
            tables=csv.DictReader(f)
            if tables.fieldnames!=['глосса','пояснение']: raise ValueError('Проверьте заголовки glossary.csv')
            for row in tables:
                if row['глосса'] in descriptions: raise ValueError('Повтор глоссы: '+row['глосса'])
                descriptions[row['глосса']]=row['пояснение']
    with glossary.open('w',encoding='utf-8-sig',newline='') as f:
        writer=csv.writer(f);writer.writerow(['глосса','пояснение'])
        writer.writerows((tag,descriptions.get(tag,'')) for tag in sorted(set(tags)|descriptions.keys()))
    print(len(ids),'texts,',len(segments),'segments,',sum(len(s['w']) for s in segments),'tokens,',sum(bool(m[3]) for s in segments for w in s['w'] for m in w[2]),'linked roots')


if __name__=='__main__':
    cli=argparse.ArgumentParser()
    for arg in ['dictionary','rules','output']:cli.add_argument(arg,type=Path)
    cli.add_argument('xml',type=Path,nargs='+')
    args=cli.parse_args()
    build(args.xml,args.dictionary,args.rules,args.output)
