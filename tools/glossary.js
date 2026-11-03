'use strict';
(()=>{
 const get=id=>document.getElementById(id);
 get('brand').outerHTML=SiteUI.brand('glossary');SiteUI.footer('glossary');SiteUI.observe();
 let data=[];
 function render(){
   const query=get('query').value.trim().normalize('NFC').toLowerCase();
   const rows=document.createDocumentFragment();let count=0;
   for(const row of data){const tag=row['глосса'],desc=row['пояснение'];
     if(![tag,desc].some(s=>s.normalize('NFC').toLowerCase().includes(query)))continue;
     const tr=document.createElement('tr'),td=document.createElement('td'),a=document.createElement('a'),definition=document.createElement('td');
     a.href='corpus.html?'+new URLSearchParams({query:tag,fields:'g',exact:'1'});a.textContent=tag;td.append(a);td.dataset.label='глосса';definition.dataset.label='пояснение';definition.textContent=desc;tr.append(td,definition);rows.append(tr);count++;
   }get('rows').replaceChildren(rows);get('status').textContent=count?'Найдено глосс: '+count:'Ничего не найдено';
 }
 get('query').oninput=render;get('clear').onclick=()=>{get('query').value='';render();get('query').focus()};
 fetch('data/glossary.csv',{cache:'no-cache'}).then(r=>{if(!r.ok)throw Error(r.status);return r.text()}).then(t=>{data=ItelmenSearch.parseCSV(t);render()}).catch(()=>{get('status').textContent='Не удалось загрузить список глосс.'});
})();
