'use strict';
(()=>{
const {$,esc,field,mount,bindSearch,load,loadError}=ItelmenUI;
mount('dictionary');
let rows=[],results=[],shown=0;
const byId=new Map();
const groups=[
 ['слово','диалект','фонетический вариант','северный диалектный вариант'],
 ['часть речи','грамматические пометы'],['толкование'],
 ['инфинитив','множественное число','общее число']
];
const labels=['Слово','Грамматика','Значение','Формы','См.'];
function seeAlso(row){
 const items=(row['См. (ID или форма)']||'').split(';').map(v=>v.trim()).filter(Boolean);
 if(!items.length)return '';
 return 'См. '+items.map(item=>{
   const target=byId.get(item);
   return target ? '<a style="color:#176da0;text-decoration:underline" href="#'+encodeURIComponent(item)+'">'+esc(target['слово'])+'</a>' : esc(item);
 }).join(', ');
}
function cells(row){
 return [...groups.map(keys=>keys.map(k=>field(row[k],k,k==='слово'?'lemma':'')).join('')),seeAlso(row)];
}
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
 if(!card.open)card.showModal();
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
load('data/Itelmen_dict.csv').then(text=>{
 rows=ItelmenSearch.parseCSV(text);
 for(const row of rows)byId.set(row['ID статьи'],row);
 openTarget();
 if(!rows.length||!('слово' in rows[0]))throw Error('Не найдены ожидаемые столбцы CSV');
 $('data-summary').textContent=`${rows.length} записей · западный диалект · исходные данные CSV`;
 bindSearch(rows,'dictionary',render);
}).catch(loadError);
})();
