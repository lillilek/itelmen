'use strict';
(()=>{
const {$,esc,field,mount,bindSearch,load,loadError}=ItelmenUI;
mount('dictionary');
let rows=[],results=[],shown=0;
const byId=new Map();
let exampleCounts={};
function examples(row){
 const id=row['id статьи'], n=exampleCounts[id];
 if(!n)return '';
 const url='corpus.html?entry='+encodeURIComponent(id);
 return '<details class="example-list" data-src="'+esc(url)+'"><summary>Примеры из корпуса ('+n+')</summary><a href="'+esc(url)+'">Открыть в корпусе</a></details>';
}
document.addEventListener('toggle',event=>{
 const box=event.target;
 if(!box.matches?.('.example-list'))return;
 const row=box.closest('tr');
 const expanded=row?.nextElementSibling?.classList.contains('example-row');
 if(!box.open){if(expanded)row.nextElementSibling.remove();return;}
 if(expanded||box.querySelector('iframe'))return;
 let host=box;
 if(row){const detail=document.createElement('tr');detail.className='example-row';host=detail.insertCell();host.colSpan=row.cells.length;row.after(detail);}
 const frame=document.createElement('iframe');
 frame.src=box.dataset.src+'&embed=1';
 frame.title='Примеры из корпуса';
 frame.style.cssText='width:100%;height:19rem;border:0';
 host.append(frame);
},true);
const groups=[
 ['слово','диалект','фонетический вариант','северный диалектный вариант'],
 ['часть речи','грамматические пометы'],['толкование'],
 ['инфинитив','множественное число','общее число']
];
const labels=['слово','грамматика','значение','формы','см.'];
function seeAlso(row){
 const items=(row['см. (id или форма)']||'').split(';').map(v=>v.trim()).filter(Boolean);
 if(!items.length)return '';
 return 'См. '+items.map(item=>{
   const target=byId.get(item);
   return target ? '<a style="color:#176da0;text-decoration:underline" href="#'+encodeURIComponent(item)+'">'+esc(target['слово'])+'</a>' : esc(item);
 }).join(', ');
}
function cells(row){
 return [...groups.map((keys,i)=>keys.map(k=>field(rvalue(row,k),k,k==='слово'?'lemma':'')).join('')+(i===0?field(row['слово (латиница)'],'латиница')+examples(row):'')),seeAlso(row)];
}
function rvalue(row,key){return row[key]}
function rowHTML(row){
 return '<tr>'+cells(row).map((v,i)=>'<td data-label="'+labels[i]+'">'+v+'</td>').join('')+'</tr>';
}
const card=document.createElement('dialog');
card.setAttribute('aria-label','Словарная статья');
document.body.append(card);
function openTarget(){
 const row=byId.get(location.hash.slice(1));
 if(!row){if(card.open)card.close();return;}
 card.innerHTML='<button type="button">Закрыть</button><h2>'+esc(row['слово'])+'</h2>'+cells(row).join('');
 card.querySelector('button').onclick=()=>card.close();
 card.style.width='min(96vw, 100rem)';card.style.maxWidth='96vw';if(!card.open)card.showModal();
}
card.addEventListener('close',()=>{
 if(byId.has(location.hash.slice(1)))history.replaceState(null,'',location.pathname+location.search);
});
window.addEventListener('hashchange',openTarget);
function append(){
 const batch=results.slice(shown,shown+150);$('rows').insertAdjacentHTML('beforeend',batch.map(id=>rowHTML(rows[id])).join(''));shown+=batch.length;
 $('more').hidden=shown>=results.length;$('shown').textContent=results.length?`Показано ${shown} из ${results.length}. Поиск охватывает весь словарь.`:'';
}
function render(ids){results=ids;shown=0;$('rows').innerHTML='';$('status').textContent=`Найдено ${ids.length} из ${rows.length} записей`;$('empty').hidden=ids.length!==0;append();}
$('more').onclick=append;
Promise.all([load('data/Itelmen_dict.csv'),load('data/examples.json','json')]).then(([text,counts])=>{
 exampleCounts=counts;
 rows=ItelmenSearch.parseCSV(text);
 for(const row of rows)byId.set(row['id статьи'],row);
 openTarget();
 if(!rows.length||!('слово' in rows[0]))throw Error('Не найдены ожидаемые столбцы CSV');
 $('data-summary').textContent=`${rows.length} записей · западный диалект · исходные данные CSV`;
 bindSearch(rows,'dictionary',render);
}).catch(loadError);
})();

