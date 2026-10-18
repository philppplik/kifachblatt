(function(){
var root=document.getElementById('hfx');if(!root)return;
var API='https://huggingface.co/api/models',EXP='&expand[]=likes&expand[]=downloads&expand[]=pipeline_tag&expand[]=createdAt&expand[]=trendingScore';
var SORTS={trend:'Trend-Score',likes:'Likes',downloads:'Downloads',new:'Neueste (unter den 100 Trendigsten)'};
var sel=document.getElementById('hf-sort'),tag=document.getElementById('hf-tag'),out=document.getElementById('hf-out'),stand=document.getElementById('hf-stand'),pb=document.getElementById('hf-print'),rb=document.getElementById('hf-reload');
var nf=function(v){return typeof v==='number'?v.toLocaleString('de-DE'):'–'};
var esc=function(s){return String(s).replace(/[&<>"]/g,function(c){return{'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]})};
function url(){var s=sel.value,t=tag.value;var q='?direction=-1';
 if(s==='likes')q+='&sort=likes&limit=20';else if(s==='downloads')q+='&sort=downloads&limit=20';else if(s==='new')q+='&sort=trendingScore&limit=100';else q+='&sort=trendingScore&limit=20';
 if(t)q+='&pipeline_tag='+encodeURIComponent(t);return API+q+EXP}
function get(u,force){var k='hfx:'+u,now=Date.now();
 if(!force){try{var c=JSON.parse(sessionStorage.getItem(k)||'null');if(c&&now-c.t<600000)return Promise.resolve(c)}catch(e){}}
 return fetch(u,{headers:{Accept:'application/json'}}).then(function(r){if(!r.ok)throw new Error('HTTP '+r.status);return r.json()}).then(function(d){var c={t:now,d:d};try{sessionStorage.setItem(k,JSON.stringify(c))}catch(e){}return c})}
function render(c){var d=c.d.slice();if(sel.value==='new')d.sort(function(a,b){return (b.createdAt||'')<(a.createdAt||'')?-1:1});d=d.slice(0,20);
 var when=new Date(c.t).toLocaleString('de-DE',{dateStyle:'medium',timeStyle:'short'});
 if(!d.length){out.innerHTML='<p class="err">Für diese Auswahl liefert die API keine Modelle.</p>';stand.textContent='';pb.disabled=true;return}
 var h='<table><thead><tr><th>#</th><th>Modell</th><th>Aufgabe</th><th class="n">Likes</th><th class="n">Downloads</th><th class="n">Trend-Score</th><th>Erstellt</th></tr></thead><tbody>';
 d.forEach(function(m,i){var u='https://huggingface.co/'+m.id;h+='<tr><td>'+(i+1)+'</td><td><a href="'+esc(u)+'" rel="noopener">'+esc(m.id)+'</a><span class="u">'+esc(u)+'</span></td><td>'+esc(m.pipeline_tag||'–')+'</td><td class="n">'+nf(m.likes)+'</td><td class="n">'+nf(m.downloads)+'</td><td class="n">'+nf(m.trendingScore)+'</td><td>'+esc((m.createdAt||'').slice(0,10))+'</td></tr>'});
 out.innerHTML=h+'</tbody></table>';
 var lab=SORTS[sel.value]+(tag.value?' · Aufgabe: '+tag.value:'');
 stand.innerHTML='Stand: '+esc(when)+' Uhr · Sortierung: '+esc(lab)+' · Quelle: <a href="https://huggingface.co/models" rel="noopener">Hugging Face, öffentliche API</a>';
 document.getElementById('hf-ts').textContent='Stand: '+when+' Uhr · Sortierung: '+lab+' · Quelle: huggingface.co (öffentliche API). Zähler der API, keine Qualitätsbewertung.';
 pb.disabled=false}
function load(force){out.innerHTML='<p class="mut">Lade Daten von Hugging Face …</p>';pb.disabled=true;
 get(url(),force).then(render).catch(function(e){out.innerHTML='<p class="err">Die Hugging-Face-API ist gerade nicht erreichbar ('+esc(e.message)+'). Bitte später erneut versuchen oder das tägliche PDF unten nutzen.</p>';stand.textContent='';})}
sel.addEventListener('change',function(){load(false)});tag.addEventListener('change',function(){load(false)});
rb.addEventListener('click',function(){load(true)});pb.addEventListener('click',function(){window.print()});
root.hidden=false;var nj=document.getElementById('hf-nojs');if(nj)nj.hidden=true;load(false);
})();
