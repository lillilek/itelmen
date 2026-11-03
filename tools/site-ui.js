'use strict';
window.SiteUI = (() => {
  const pages = [['dictionary','index.html','Словарь'],['corpus','corpus.html','Корпус'],['glossary','glossary.html','Список глосс']];
  const nav = mode => pages.map(([id,url,title]) => '<a href="'+url+'" '+(mode===id?'aria-current="page"':'')+'>'+title+'</a>').join('');
  const brand = mode => '<div class="brand-row"><div><p class="eyebrow">Ительменский язык · словарь и корпус</p><h1>Ительменский язык</h1></div><nav aria-label="Разделы сайта">'+nav(mode)+'</nav></div>';
  const groups = {'Кириллица':'ӄ ӽ ӈ ԓ ӆ љ њ ә ӑ ў ԝ қ ҳ ң ʔ ʼ ˚','Латиница':'č χ ŋ ƚ ł ɬ ʎ ɲ β ə ʔ ʼ ʲ ʷ ˠ ă ǎ ŏ ŭ ɣ ʂ ʐ ɕ ː t͡s ◌́ ◌̀'};
  function keyboard(query, extra=[]){
    const row=query.closest('.search-row'),toggle=document.createElement('button'),box=document.createElement('div');
    toggle.textContent='Клавиатура';toggle.type='button';toggle.setAttribute('aria-expanded','false');toggle.setAttribute('aria-controls','letter-panel');
    box.className='letter-panel';box.id='letter-panel';box.hidden=true;row.append(toggle);row.after(box);
    let target=query;
    for(const input of [query,...extra])input.addEventListener('focus',()=>target=input);
    for(const [name,keys] of Object.entries(groups)){
      const group=document.createElement('div'),label=document.createElement('span');label.textContent=name;group.append(label);
      for(const key of keys.split(' ')){
        const button=document.createElement('button');button.type='button';button.textContent=key;button.setAttribute('aria-label','Вставить '+key);button.onclick=()=>{
          target.focus();target.setRangeText(key.replace('◌',''),target.selectionStart,target.selectionEnd,'end');target.dispatchEvent(new Event('input',{bubbles:true}));
        };group.append(button);
      }box.append(group);
    }
    toggle.onclick=()=>{box.hidden=!box.hidden;toggle.setAttribute('aria-expanded',String(!box.hidden));};
  }
  function footer(mode){document.querySelector('footer').innerHTML='Ительменский язык · '+pages.map(([id,url,title])=>'<a href="'+url+'">'+title+'</a>').join(' · ');}
  function observe(){const h=document.querySelector('#site-header');new ResizeObserver(()=>document.documentElement.style.setProperty('--header-height',h.offsetHeight+'px')).observe(h);}
  return {brand,keyboard,footer,observe};
})();
