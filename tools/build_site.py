"""Rebuild the local reader. python tools/build_site.py (from any directory)."""
from pathlib import Path
import csv,json,shutil,re,argparse
from build_reader import build,transliterate,FORM_FIELDS

def package(root,out,dictionary):
    work=Path(__file__).resolve().parent
    (out/'data').mkdir(parents=True,exist_ok=True)
    shutil.copytree(root/'assets',out/'assets',dirs_exist_ok=True)
    for src,dst in [('dictionary.html','index.html'),('glossary.html','glossary.html'),('see-app.js','assets/app.js'),('dict-shared.js','assets/shared.js'),('site-ui.js','assets/site-ui.js'),('site-ui.css','assets/site-ui.css'),('glossary.js','assets/glossary.js')]:
        shutil.copy2(work/src,out/dst)
    p=out/'assets/search.js'
    s=p.read_text(encoding='utf8')
    start=s.index('const DICT_FIELDS = ')+len('const DICT_FIELDS = ')
    end=s.index(';',start)
    fields=[f for f in json.loads(s[start:end]) if f['id'] in {'f'+str(i) for i in range(10)}]
    fields.append(dict(id='lat',label='латиница',keys=[x+' (латиница)' for x in FORM_FIELDS],word=True,default=True))
    p.write_text(s[:start]+json.dumps(fields,ensure_ascii=False)+s[end:],encoding='utf8')
    with (out/'assets/style.css').open('a',encoding='utf8') as f:
        f.write('\nbody{color:#172f4a;background:#edf6ff}#site-header{background:#e0efff;color:#172f4a}a,.lemma{color:#165888}dialog{max-width:min(52rem,96vw)}')
    rules=work/'reader-rules.json'
    mapping=dict(sorted(json.loads(rules.read_text(encoding='utf8')).items(),key=lambda kv:-len(kv[0])))
    with dictionary.open(encoding='utf-8-sig',newline='') as f:
        reader=csv.DictReader(f)
        head=[h.lower() for h in reader.fieldnames if h and h.lower() not in {'ссылка','буквы без правила','лемма flex (точное совпадение)'}]
        rows=[{k.lower():v for k,v in row.items() if k and k.lower() in head} for row in reader]
    for r in rows:
        for k in FORM_FIELDS:r[k+' (латиница)']=transliterate(r[k],mapping)
    csvfile=out/'data/Itelmen_dict.csv'
    with csvfile.open('w',encoding='utf-8-sig',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=head);writer.writeheader();writer.writerows(rows)
    build(sorted((root/'.private/texts').glob('*.xml')),csvfile,rules,out/'corpus.html')

if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--root',type=Path,default=Path(__file__).resolve().parent.parent)
    parser.add_argument('--output',type=Path)
    parser.add_argument('--dictionary',type=Path)
    a=parser.parse_args()
    package(a.root,a.output or a.root/'dist',a.dictionary or a.root/'.private/dictionary-source.csv')
