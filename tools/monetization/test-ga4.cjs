/* Rich-Consent QA kfb: jede HTTPS-Anfrage abgefangen, nie an Google gesendet.
   NODE_PATH=... node tools/monetization/test-ga4.cjs (ROOT, PREFIX=kfb, ID=G-75G1VNDHJW) */
const {chromium}=require('playwright'),http=require('http'),fs=require('fs'),path=require('path'),assert=require('assert');
let root=process.env.ROOT||path.resolve(__dirname,'../..'),prefix=process.env.PREFIX||'kfb',id=process.env.ID||'G-75G1VNDHJW',shots=process.env.SCREENSHOT_DIR||'/tmp/ga3-'+prefix;fs.mkdirSync(shots,{recursive:true});
let server=http.createServer((req,res)=>{let f=path.join(root,decodeURI(req.url.split('?')[0]));if(f.endsWith('/'))f+='index.html';if(!path.extname(f)&&fs.existsSync(f+'.html'))f+='.html';try{res.setHeader('Content-Type',f.endsWith('.js')?'text/javascript':f.endsWith('.css')?'text/css':f.endsWith('.svg')?'image/svg+xml':'text/html');res.end(fs.readFileSync(f));}catch(e){res.statusCode=404;res.end('missing')}});
(async()=>{await new Promise(r=>server.listen(0,'127.0.0.1',r));let b=await chromium.launch({executablePath:'/usr/bin/google-chrome',args:['--no-sandbox']}),n=0;function ok(x,m){assert(x,m);n++}
async function ctx0(w){let c=await b.newContext({viewport:{width:w,height:900}}),remote=[];await c.route('https://**/*',r=>{remote.push(r.request().url());return r.fulfill({contentType:'application/javascript',body:'/* intercepted */'})});return{c,remote}}
try{
for(let width of [1440,390]){
  let {c,remote}=await ctx0(width),page=await c.newPage(),base='http://127.0.0.1:'+server.address().port;
  await page.goto(base+'/cookies?q=private@example.test');ok(remote.length===0,'no remote pre-consent');
  ok(!(await page.locator('#'+prefix+'-statistics').isDisabled()),'statistics selectable');ok(await page.locator('#'+prefix+'-advertising').isDisabled(),'advertising locked');
  ok(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),'no h-overflow');
  await page.screenshot({path:shots+'/drawer-'+width+'.png'});
  await page.locator('[data-consent="reject"]').click();await page.reload();ok(remote.length===0,'reject tag-free');
  await page.locator('[data-'+prefix+'-consent-open]').click();await page.locator('#'+prefix+'-statistics').check();await page.locator('[data-consent="save"]').click();
  await page.waitForFunction(()=>document.querySelector('script[src*="googletagmanager"]'));
  ok(remote.length===1&&remote[0].includes(id),'one gtag load, property id');
  let q=await page.evaluate(()=>dataLayer.map(x=>Array.from(x))),cf=q.find(x=>x[0]==='config')[2],v=q.find(x=>x[0]==='event'&&x[1]==='page_view')[2];
  ok(cf.cookie_expires===15552000&&cf.cookie_update===false,'180d fixed');ok(cf.allow_google_signals===false&&cf.allow_ad_personalization_signals===false,'no signals');
  ok(cf.send_page_view===false,'manual page_view');ok(cf.cookie_domain==='127.0.0.1','host-only');
  ok(q[0][2].analytics_storage==='denied'&&q[1][2].analytics_storage==='granted','consent sequence');
  ok(v.content_group==='rechtliches','group cookies');ok(!v.page_location.includes('?'),'query stripped');ok(v.page_referrer==='','referrer empty');
  await page.goto(base+'/?utm_source=rss&utm_medium=email&utm_campaign=nicht-freigegeben&q=geheim');
  let v2=await page.evaluate(()=>dataLayer.filter(x=>x[0]==='event'&&x[1]==='page_view').map(x=>Array.from(x)[2]).pop());
  ok(v2.content_group==='startseite','group start');ok(v2.page_location.includes('utm_source=rss')&&v2.page_location.includes('utm_medium=email'),'utm allowlist');
  ok(!v2.page_location.includes('nicht-freigegeben')&&!v2.page_location.includes('geheim'),'campaign+q dropped');
  for(const [route,grp] of [['/llm-kostenrechner','rechner'],['/modell-atlas','modell-atlas'],['/rag-selbst-bauen','fachartikel'],['/glossar','wissen']]){
    await page.goto(base+route);let vv=await page.evaluate(()=>dataLayer.filter(x=>x[0]==='event'&&x[1]==='page_view').map(x=>Array.from(x)[2]).pop());ok(vv.content_group===grp,'group '+route);
  }
  await page.goto(base+'/llm-kostenrechner');
  ok(await page.evaluate(()=>dataLayer.some(x=>x[0]==='event'&&x[1]==='tool_used')),'tool_used on rechner');
  await page.goto(base+'/rag-selbst-bauen');await page.evaluate(()=>window.scrollTo(0,document.body.scrollHeight));await page.waitForTimeout(600);
  ok(await page.evaluate(()=>dataLayer.some(x=>x[0]==='event'&&x[1]==='scroll_percent')),'scroll depth');
  ok(await page.evaluate(()=>{let a=document.createElement('a');a.href='/portrait-pdf/test.pdf';a.textContent='x';document.body.appendChild(a);window.addEventListener('click',e=>e.preventDefault(),{once:true});a.dispatchEvent(new MouseEvent('click',{bubbles:true,cancelable:true}));let r=dataLayer.some(x=>x[0]==='event'&&x[1]==='file_download'&&x[2].file_extension==='pdf');a.remove();return r}),'file_download allowlisted');
  ok(await page.evaluate(()=>{let a=document.createElement('a');a.href='https://example-tracking.invalid/x';a.textContent='x';document.body.appendChild(a);window.addEventListener('click',e=>e.preventDefault(),{once:true});a.dispatchEvent(new MouseEvent('click',{bubbles:true,cancelable:true}));let r=!dataLayer.some(x=>x[0]==='event'&&x[1]==='outbound_click');a.remove();return r}),'outbound blocked (empty allowlist)');
  let before=remote.filter(u=>u.includes('googletagmanager')).length;
  await page.evaluate(()=>document.cookie='_ga=fixture;path=/');await page.locator('[data-'+prefix+'-consent-open]').click();await page.locator('[data-consent="reject"]').click();
  await page.waitForFunction(()=>!window.dataLayer);await page.reload();await page.waitForTimeout(300);
  ok(!(await c.cookies()).some(x=>x.name==='_ga'),'_ga removed');ok(remote.filter(u=>u.includes('googletagmanager')).length===before,'no reload after withdrawal');
  await page.goto(base+'/datenschutz');let ds=await page.locator('#ga4-disclosure').textContent();
  ok(ds.includes('14 Monate'),'retention');ok(ds.includes('LLM-Kostenrechners'),'tool bullet');ok(ds.includes('niemals deine Eingaben'),'no-inputs promise');
  ok((await page.locator('body').textContent()).includes('keine Konto-Registrierung'),'registration wording');
  ok(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),'no overflow dsg');
  await page.locator('#ga4-disclosure').scrollIntoViewIfNeeded();await page.screenshot({path:shots+'/privacy-'+width+'.png'});
  await page.goto(base+'/cookies');ok((await page.locator('body').textContent()).includes('_ga'),'ga cookies listed');
  await c.close();
}
let {c:c2,remote:r2}=await ctx0(1440),p2=await c2.newPage(),base2='http://127.0.0.1:'+server.address().port;
await p2.goto(base2+'/');await p2.locator('[data-consent="all"]').click();await p2.waitForFunction(()=>document.querySelector('script[src*="googletagmanager"]'));
await p2.goto(base2+'/tagesbericht-bestaetigt');await p2.waitForTimeout(400);
ok(r2.filter(u=>u.includes('googletagmanager')).length===1,'excluded route: no new tag');
ok(await p2.evaluate(()=>document.querySelectorAll('script[src*="googletagmanager"]').length===0),'no tag on excluded route');
await c2.close();
console.log(prefix+': '+n+' rich assertions; all HTTPS intercepted')}finally{await b.close();server.close()}})().catch(e=>{console.error(e);server.close();process.exitCode=1});
