(function(){
var inp=document.getElementById('sq'),list=document.getElementById('sresults'),stat=document.getElementById('sstatus');
if(!inp||!list)return;
var docs=[],vocab=[];
function norm(s){return (s||'').toLowerCase().replace(/ä/g,'ae').replace(/ö/g,'oe').replace(/ü/g,'ue').replace(/ß/g,'ss').normalize('NFD').replace(/[\u0300-\u036f]/g,'')}
function compact(s){return norm(s).replace(/[^a-z0-9]+/g,'')}
function lev1(a,b){var la=a.length,lb=b.length;if(Math.abs(la-lb)>1)return false;var i=0,j=0,d=0;while(i<la&&j<lb){if(a[i]===b[j]){i++;j++}else{d++;if(d>1)return false;if(la>lb)i++;else if(lb>la)j++;else{i++;j++}}}if(i<la||j<lb)d++;return d<=1}
function typo(t,w){if(lev1(t,w))return true;if(w.length>t.length+1)return lev1(t,w.slice(0,t.length))||lev1(t,w.slice(0,t.length+1));return false}
function esc(s){var d=document.createElement('div');d.textContent=s;return d.innerHTML}
function prep(ds){docs=ds.map(function(o){var ti=norm(o.t),tg=norm((o.k||'')+' '+(o.g||'')),bo=norm((o.d||'')+' '+(o.x||''));return{o:o,ti:ti,tg:tg,bo:bo,tc:ti.replace(/[^a-z0-9]+/g,''),bc:(tg+' '+bo).replace(/[^a-z0-9]+/g,'')}});
var seen={},v=[];docs.forEach(function(e){(e.ti+' '+e.tg+' '+e.bo).split(/[^a-z0-9]+/).forEach(function(w){if(w.length>3&&!seen[w]){seen[w]=1;v.push(w)}})});vocab=v}
function corrections(t){var c=[t];if(t.length>3){for(var j=0;j<vocab.length;j++){var w=vocab[j];if(w!==t&&typo(t,w)){c.push(w);if(c.length>25)break}}}return c}
function run(){var q=inp.value.trim();list.innerHTML='';
if(q.length<2){stat.textContent='';return}
var tokens=norm(q).split(/[^a-z0-9]+/).filter(function(t){return t.length>1});
if(!tokens.length){stat.textContent='';return}
var corr=tokens.map(corrections),res=[];
docs.forEach(function(e){var score=0,ok=true;
for(var i=0;i<corr.length;i++){var s=0;
for(var k=0;k<corr[i].length;k++){var t=corr[i][k],f=k===0?1:0.34,tc=compact(t);
if(e.ti.indexOf(t)>=0)s=Math.max(s,10*f);else if(e.tg.indexOf(t)>=0)s=Math.max(s,6*f);else if(e.bo.indexOf(t)>=0)s=Math.max(s,3*f);
else if(tc.length>1&&e.tc.indexOf(tc)>=0)s=Math.max(s,4*f);else if(tc.length>1&&e.bc.indexOf(tc)>=0)s=Math.max(s,2*f)}
if(s<0.5){ok=false;break}score+=s}
if(ok)res.push([score,e.o])});
res.sort(function(a,b){return b[0]-a[0]||((b[1].ts||0)-(a[1].ts||0))});
stat.textContent=res.length?(res.length===1?'1 Treffer':res.length+' Treffer'):'Keine Treffer für „'+q+'“. Tipp: Umlaute und kleine Tippfehler werden verziehen.';
list.innerHTML=res.slice(0,50).map(function(r){var o=r[1];
return '<li><a class="rt" href="'+o.u+'"'+(o.ext?' target="_blank" rel="noopener"':'')+'>'+esc(o.t)+(o.ext?' ↗':'')+'</a>'+(o.d?'<p>'+esc(o.d)+'</p>':'')+'<div class="sm">'+esc(o.k||'')+(o.dt?' · '+esc(o.dt):'')+(o.ext?' · externe Quelle':'')+'</div></li>'}).join('')}
var tm;inp.addEventListener('input',function(){clearTimeout(tm);tm=setTimeout(run,120)});
var f=inp.closest('form');if(f)f.addEventListener('submit',function(e){e.preventDefault();run()});
try{var mq=new URLSearchParams(location.search).get('q');if(mq)inp.value=mq}catch(e){}
fetch('/search-index.json').then(function(r){if(!r.ok)throw 0;return r.json()}).then(function(j){prep(j.docs||j);run()}).catch(function(){stat.textContent='Der Suchindex konnte nicht geladen werden.'});
})();
