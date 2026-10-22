(function(){
  // Set the backend base URL in <meta name="kfb-lw-api" content="https://..."> or window.KFB_LW_API.
  var m=document.querySelector('meta[name="kfb-lw-api"]'),API=(window.KFB_LW_API||(m&&m.content)||'https://daily-hob-newsletter.vercel.app/lw').replace(/\/$/,'');
  var KEY='kfb-lw-k',DAYS=365;
  function get(){try{var r=JSON.parse(localStorage.getItem(KEY)||'null');if(r&&r.exp>Date.now())return r.k}catch(e){}return null}
  function set(k){try{localStorage.setItem(KEY,JSON.stringify({k:k,exp:Date.now()+DAYS*864e5}))}catch(e){}}
  var path=location.pathname.replace(/\.html$/,'');
  // 1) Report breakers: remembered subscribers go straight to the PDF, everyone else to the sign-up page.
  document.querySelectorAll('a[href="/tagesbericht-anmelden"]:not(.lw-go)').forEach(function(a){
    var k=get();a.href=(k&&API)?API+'/api/pdf?k='+encodeURIComponent(k):'/tagesbericht-anmelden';
  });
  // 2) Sign-up form
  var f=document.getElementById('lw-form');
  if(f)f.addEventListener('submit',function(e){e.preventDefault();var msg=document.getElementById('lw-msg'),b=f.querySelector('button');
    function show(t,err){msg.hidden=false;msg.className='lw-msg'+(err?' lw-err':'');msg.textContent=t}
    var em=f.email.value.trim();
    if(!/^\S+@\S+\.\S{2,}$/.test(em))return show('Bitte gib eine gültige E-Mail-Adresse ein.',1);
    if(!f.consent.checked)return show('Bitte stimme dem Erhalt des Tagesberichts per E-Mail zu (Checkbox).',1);
    if(!API)return show('Die Anmeldung ist noch nicht freigeschaltet.',1);
    b.disabled=true;
    fetch(API+'/api/'+(f.getAttribute('data-ep')||'subscribe'),{method:'POST',headers:{'content-type':'application/json'},body:JSON.stringify({email:em,consent:true,website:f.website.value})})
      .then(function(r){return r.json()}).then(function(j){b.disabled=false;
        if(j.ok){var ep=f.getAttribute('data-ep');show(ep==='tksub'||ep==='atlassub'?'Fast geschafft: Wir haben dir eine E-Mail geschickt. Bitte klicke auf den Link darin (auch im Spam-Ordner nachsehen), dann kannst du '+(ep==='atlassub'?'das Datenpaket':'das Toolkit')+' herunterladen.':'Fast geschafft: Wir haben dir eine Bestätigungsmail geschickt. Bitte klicke auf den Link darin (auch im Spam-Ordner nachsehen).');}
        else show('Das hat nicht geklappt. Bitte prüfe die Eingaben.',1)})
      .catch(function(){b.disabled=false;show('Verbindungsfehler. Bitte versuche es später erneut.',1)});
  });
  // 2b) Toolkit page: remembered subscribers get the download link directly.
  var kn=document.getElementById('tk-known');if(kn){var kk=get();if(kk){kn.hidden=false;kn.querySelector('a').href=API+'/api/tkdl?k='+encodeURIComponent(kk)}}
  // 2c) Toolkit confirmation page
  if(path==='/toolkit-bestaetigt'){
    var th=/[#&]k=([^&]+)/.exec(location.hash),tok=document.getElementById('lw-ok'),tbad=document.getElementById('lw-bad');
    if(th&&API){var tk=decodeURIComponent(th[1]);history.replaceState(null,'',location.pathname);tok.hidden=false;document.getElementById('lw-dl').href=API+'/api/tkdl?k='+encodeURIComponent(tk);
      document.getElementById('lw-keep').addEventListener('click',function(){set(tk);location.href=API+'/api/tkdl?k='+encodeURIComponent(tk)});
    }else tbad.hidden=false;
  }
  // 2d) Atlas data package confirmation page
  if(path==='/atlas-daten-bestaetigt'){
    var ah=/[#&]k=([^&]+)/.exec(location.hash),aok=document.getElementById('lw-ok'),abad=document.getElementById('lw-bad');
    if(ah&&API){var ak=decodeURIComponent(ah[1]);history.replaceState(null,'',location.pathname);aok.hidden=false;document.getElementById('lw-dl').href=API+'/api/atlasdl?k='+encodeURIComponent(ak);
      document.getElementById('lw-keep').addEventListener('click',function(){set(ak);location.href=API+'/api/atlasdl?k='+encodeURIComponent(ak)});
    }else abad.hidden=false;
  }
  // 3) Confirmation page: token comes in the URL fragment; only an active click stores it (Option B).
  if(path==='/tagesbericht-bestaetigt'){
    var h=/[#&]k=([^&]+)/.exec(location.hash),ok=document.getElementById('lw-ok'),bad=document.getElementById('lw-bad');
    if(h&&API){var k=decodeURIComponent(h[1]);history.replaceState(null,'',location.pathname);ok.hidden=false;
      var dl=document.getElementById('lw-dl');dl.href=API+'/api/pdf?k='+encodeURIComponent(k);
      document.getElementById('lw-keep').addEventListener('click',function(){set(k);location.href=dl.href});
    }else bad.hidden=false;
  }
})();
