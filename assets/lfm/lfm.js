(function(){
var M=window.LFM_MODELS||[];if(!M.length)return;
function el(t,a,c){var e=document.createElement(t);if(a)for(var k in a){if(k==='text')e.textContent=a[k];else e.setAttribute(k,a[k])}(c||[]).forEach(function(x){e.appendChild(typeof x==='string'?document.createTextNode(x):x)});return e}
function fmt(n,d){return n.toLocaleString('de-DE',{minimumFractionDigits:d==null?2:d,maximumFractionDigits:d==null?2:d})}
function byId(i){return M.filter(function(m){return m.id===i})[0]}
function sel(id,label,opts,val){var s=el('select',{id:id});opts.forEach(function(o){var op=el('option',{value:o[0],text:o[1]});if(o[0]===val)op.selected=true;s.appendChild(op)});return el('div',null,[el('label',{'for':id,text:label}),s])}
function q(m,tag){return (m.quants||[]).filter(function(x){return x.tag===tag})[0]}
/* Erklaer-Simulator */
var ex=document.getElementById('lfm-explain');
if(ex){var cur=M[0].id;var tabs=el('div',{'class':'lfm-tabs',role:'group','aria-label':'Modell wählen'});var out=el('div',{'aria-live':'polite'});
function drawEx(){tabs.innerHTML='';M.forEach(function(m){var b=el('button',{type:'button','aria-pressed':m.id===cur?'true':'false',text:m.name});b.onclick=function(){cur=m.id;drawEx()};tabs.appendChild(b)});
var m=byId(cur);out.innerHTML='';var r=el('div',{'class':'lfm-res'});r.appendChild(el('h3',{text:m.name+' · '+m.role}));r.appendChild(el('p',{text:m.for}));
var dl=el('dl');[['Eingabe',m.in],['Ausgabe',m.out],['Parameter',m.params_note||'nicht angegeben'],['Kontextfenster',m.ctx||'nicht geprüft']].forEach(function(p){dl.appendChild(el('dt',{text:p[0]}));dl.appendChild(el('dd',{text:p[1]}))});r.appendChild(dl);
var qs=m.quants||[];if(!qs.length){}if(qs.length){r.appendChild(el('h3',{text:'Formate und Dateigröße'}));var ul=el('ul',{'class':'lfm-list'});qs.forEach(function(x){var t=x.tag+': '+fmt(x.gb)+' GB Datei'+(x.verified?' (laut Ollama-Library/Hugging Face)':' (Näherung, für dieses Modell nicht geprüft)');ul.appendChild(el('li',{text:t}))});r.appendChild(ul);if(m.extra_gb)r.appendChild(el('p',{'class':'lfm-note',text:(m.extra_note||'Zusatzdateien')+'.'}));r.appendChild(el('p',{'class':'lfm-note',text:'Das sind Dateigrößen zum Herunterladen. Der Speicherbedarf beim Laufen ist höher, siehe Gerätecheck.'}))}
if(!qs.length&&m.id!=='d1'){r.appendChild(el('p',{'class':'lfm-note',text:'Für dieses Modell liegen hier keine geprüften Dateigrößen je Format vor. '+(m.extra_note?m.extra_note+'.':'')+' Sieh dir die Tags in der Ollama-Library an. Deshalb fehlt es im Gerätecheck.'}))}if(m.id==='d1')r.appendChild(el('p',{'class':'lfm-note',text:'Für d1 liegt hier keine geprüfte Größenangabe vor, deshalb fehlt es im Gerätecheck. d1 antwortet nicht mit Text, sondern mit Wahrscheinlichkeiten für eine Fragenliste. Es ist kein Chatmodell.'}));
out.appendChild(r)}
ex.appendChild(tabs);ex.appendChild(out);drawEx()}
/* Geraetecheck: nur Speicherschaetzung */
var ck=document.getElementById('lfm-check');
if(ck){var g=el('div',{'class':'lfm-grid'});
var DEV=[['phone','Handy (Android/iPhone)',50],['unified','Apple Silicon (gemeinsamer Speicher)',30],['gpu','PC mit dedizierter Grafikkarte (VRAM)',10],['cpu','PC nur mit Prozessor (Arbeitsspeicher)',35]];
g.appendChild(sel('c-model','Modell',M.filter(function(m){return (m.quants||[]).length}).map(function(m){return [m.id,m.name]}),'lfm3'));
g.appendChild(el('div',null,[el('label',{'for':'c-quant',text:'Format'}),el('select',{id:'c-quant'})]));
g.appendChild(sel('c-dev','Gerätetyp (setzt nur einen Vorschlag für „schon belegt“)',DEV.map(function(d){return [d[0],d[1]]}),'unified'));
g.appendChild(el('div',null,[el('label',{'for':'c-mem',text:'Gesamtspeicher des Geräts in GB (Arbeitsspeicher, bei Grafikkarte: VRAM)'}),el('input',{id:'c-mem',type:'number',min:'1',max:'1024',step:'1',value:'16',required:'required',inputmode:'decimal'})]));
g.appendChild(el('div',null,[el('label',{'for':'c-ctx',text:'Kontext in Tokens'}),el('select',{id:'c-ctx'})]));
g.appendChild(el('div',null,[el('label',{'for':'c-res',text:'Schon belegt (System, Apps) in GB'}),el('input',{id:'c-res',type:'number',min:'0',max:'1024',step:'0.5',value:'6',inputmode:'decimal'})]));
g.appendChild(el('div',null,[el('label',{'for':'c-oh',text:'Zusatz für Software (Annahme) in GB'}),el('input',{id:'c-oh',type:'number',min:'0',max:'16',step:'0.25',value:'0.5',inputmode:'decimal'})]));
ck.appendChild(g);var res=el('div',{id:'c-out'});ck.appendChild(res);var live=el('div',{role:'status','aria-live':'polite','class':'lfm-sr',id:'c-live'});ck.appendChild(live);var lt=null;function say(t){clearTimeout(lt);lt=setTimeout(function(){live.textContent=t},900)}
var $=function(i){return document.getElementById(i)};
var defRes={phone:6,unified:6,gpu:1,cpu:6};
function fillQ(){var m=byId($('c-model').value);var s=$('c-quant');s.innerHTML='';(m.quants||[]).forEach(function(x){s.appendChild(el('option',{value:x.tag,text:x.tag}))});
var c=$('c-ctx');c.innerHTML='';[4096,8192,32768,131072,262144].filter(function(v){return v<=(m.ctx_max||32768)}).forEach(function(v){c.appendChild(el('option',{value:String(v),text:v>=1024?(v/1024)+'K':v}))})}
function calc(){var m=byId($('c-model').value),x=q(m,$('c-quant').value);res.innerHTML='';
if(!x){res.appendChild(el('p',{role:'alert','class':'lfm-note',text:'Für diese Auswahl liegen keine geprüften Dateigrößen vor. Bitte ein anderes Modell oder Format wählen.'}));return}
var f=[['c-mem',1,1024,'Speicher des Geräts'],['c-res',0,1024,'Schon belegt'],['c-oh',0,16,'Software-Aufschlag']],vals={},bad=[];
f.forEach(function(c){var i=$(c[0]),v=parseFloat(String(i.value).replace(',','.'));var ok=isFinite(v)&&v>=c[1]&&v<=c[2];i.setAttribute('aria-invalid',ok?'false':'true');if(ok)i.removeAttribute('aria-describedby');else i.setAttribute('aria-describedby','c-err');if(ok)vals[c[0]]=v;else bad.push(c[3]+': Zahl von '+c[1]+' bis '+c[2]+' GB')});
if(bad.length){res.appendChild(el('p',{role:'alert',id:'c-err','class':'lfm-note lfm-err',text:'Bitte prüfe die Eingaben. '+bad.join('; ')+'.'}));return}
var mem=vals['c-mem'],rs=vals['c-res'],oh=vals['c-oh'],ctx=parseInt($('c-ctx').value,10);
var kv=12288*ctx/1e9;var weights=x.gb;var need=weights+kv+oh;var avail=mem-rs;
var v,cls;var gap=avail-need;if(avail<=0){v='Kein freier Speicher bei diesen Angaben';cls='lfm-v-no'}else if(need>avail){v='Passt rechnerisch nicht';cls='lfm-v-no'}else if(gap<1){v='Knapp: rechnerisch gedeckt, tatsächlicher Bedarf unklar';cls='lfm-v-tight'}else{v='Rechnerisch gedeckt, tatsächlicher Bedarf bleibt unklar';cls='lfm-v-ok'}
var r=el('div',{'class':'lfm-res'});r.appendChild(el('h3',null,[el('span',{'class':cls,text:v})]));
var pct=avail>0?Math.min(100,need/avail*100):100;r.appendChild(el('div',{'class':'lfm-bar',role:'img','aria-label':'Geschätzter Bedarf im Verhältnis zum freien Speicher: '+(need>avail?'über 100':fmt(pct,0))+' Prozent'},[el('i',{style:'width:'+pct+'%'})]));
var dl=el('dl');[['Datei (Gewichte)',fmt(weights)+' GB'],['Kontext-Speicher (KV-Cache), Mindestwert laut Architektur',fmt(kv)+' GB'],['Aufschlag der Software (unbelegte Annahme)',fmt(oh)+' GB'],['Geschätzter Bedarf',fmt(need)+' GB'],['Frei laut deinen Angaben',avail>0?fmt(avail)+' GB':'0 GB'],['Abstand (frei minus Bedarf)',fmt(avail-need)+' GB']].forEach(function(p){dl.appendChild(el('dt',{text:p[0]}));dl.appendChild(el('dd',{text:p[1]}))});r.appendChild(dl);
r.appendChild(el('p',{'class':'lfm-note',text:'Das ist eine Rechnung mit deinen Annahmen, keine Zusage und keine Messung. Ein kleiner Abstand ist riskant, weil Software und System mehr brauchen können. Eine Geschwindigkeit sagt dieser Check nicht voraus. Sie lässt sich nur auf deinem Gerät mit deiner Software messen.'}));
var d=el('details',{'class':'lfm-assume'});d.appendChild(el('summary',{text:'Annahmen und Grenzen anzeigen'}));
var ul=el('ul',{'class':'lfm-list'});[
'Dateigröße: laut Ollama-Library und Hugging Face für das Textmodell LFM3-1.7B. Das ist die Downloadgröße, nicht der gesamte Speicherbedarf.',
'Kontext-Speicher: aus der offiziellen Konfiguration von LFM3-1.7B berechnet (6 globale Attention-Schichten, 4 KV-Köpfe, Kopfgröße 128, 16 Bit): 12.288 Byte pro Token, bei 128K etwa 1,6 GB; Liquid nennt im Blogbeitrag zu LFM3 ebenfalls 1,6 GB. Das ist ein Mindestwert. Wie Ollama, llama.cpp oder MLX den Cache tatsächlich anlegen, ist unbekannt und kann mehr sein.',
'Bewertung: „Knapp“ heißt, dass weniger als 1 GB Abstand bleibt. Das ist eine von uns gewählte Anzeigegrenze, keine technische Schwelle. Auch bei großem Abstand garantiert die Rechnung nicht, dass es läuft.','Aufschlag der Software und „schon belegt“ sind frei wählbare Annahmen, keine gemessenen Werte. Der Gerätetyp setzt nur einen Vorschlag für „schon belegt“. Er ändert die Rechnung sonst nicht.',
'Bild-, Video- und Audio-Modelle fehlen hier, weil keine geprüften Dateigrößen je Paket vorliegen.',
'Je nach Gerät und Software kann ein Teil der Berechnung in den Hauptspeicher oder auf den Prozessor ausweichen. Das ändert den nötigen Speicher und das Tempo und wird hier nicht modelliert.',
'Kontextfenster laut Quelle: '+(m.ctx||'nicht geprüft')+'.'].forEach(function(t){ul.appendChild(el('li',{text:t}))});d.appendChild(ul);r.appendChild(d);say(v+'. Geschätzter Bedarf '+fmt(need)+' Gigabyte, frei '+(avail>0?fmt(avail):'0')+' Gigabyte.');res.appendChild(r)}
$('c-model').addEventListener('change',function(){fillQ();calc()});
['c-quant','c-ctx','c-mem','c-res','c-oh'].forEach(function(i){$(i).addEventListener('input',calc);$(i).addEventListener('change',calc)});
$('c-dev').addEventListener('change',function(){$('c-res').value=defRes[$('c-dev').value];calc()});
fillQ();calc()}
})();
