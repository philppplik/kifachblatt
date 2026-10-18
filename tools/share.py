import urllib.parse as _up
def share_block(url, title, brand):
    q = _up.quote
    u, t = q(url, safe=''), q(title, safe='')
    def svg(inner): return '<svg viewBox="0 0 24 24" width="18" height="18" aria-hidden="true" focusable="false">%s</svg>' % inner
    def tx(s, size=13): return svg('<text x="12" y="16.5" text-anchor="middle" font-family="Arial,Helvetica,sans-serif" font-weight="700" font-size="%d" fill="currentColor">%s</text>' % (size, s))
    links = [
        ('X', 'Auf X teilen', 'https://twitter.com/intent/tweet?url=%s&text=%s' % (u, t), svg('<path d="M5 4l14 16M19 4L5 20" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" fill="none"/>')),
        ('LinkedIn', 'Auf LinkedIn teilen', 'https://www.linkedin.com/sharing/share-offsite/?url=%s' % u, tx('in')),
        ('WhatsApp', 'Per WhatsApp teilen', 'https://wa.me/?text=%s%%20%s' % (t, u), svg('<path d="M12 3.5a8.5 8.5 0 0 0-7.3 12.8L3.5 20.5l4.3-1.1A8.5 8.5 0 1 0 12 3.5z" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linejoin="round"/><path d="M9 8.5c0 3.5 2.7 6.5 6.5 6.5l1-1.8-2-1-1 .8c-1-.4-1.9-1.300-2.300-2.300l.8-1-1-2z" fill="currentColor"/>')),
        ('Facebook', 'Auf Facebook teilen', 'https://www.facebook.com/sharer/sharer.php?u=%s' % u, tx('f', 16)),
        ('Reddit', 'Auf Reddit teilen', 'https://www.reddit.com/submit?url=%s&title=%s' % (u, t), tx('R', 14)),
        ('E-Mail', 'Per E-Mail teilen', 'mailto:?subject=%s&body=%s' % (t, u), svg('<rect x="3.5" y="6" width="17" height="12" rx="2" fill="none" stroke="currentColor" stroke-width="1.8"/><path d="M4 7.500l8 6 8-6" fill="none" stroke="currentColor" stroke-width="1.8"/>')),
    ]
    items = ''.join('<li><a class="sh-b" href="%s" target="_blank" rel="noopener noreferrer nofollow" aria-label="%s (öffnet in neuem Tab)" title="%s">%s<span>%s</span></a></li>' % (h.replace('&', '&amp;'), lab, lab, ic, nm) for nm, lab, h, ic in links)
    items += ('<li><button type="button" class="sh-b" data-copy="%s" aria-label="Link kopieren" title="Link kopieren">%s<span>Link kopieren</span></button></li>'
              % (url, svg('<path d="M10 14a4 4 0 0 0 5.700 0l3-3a4 4 0 0 0-5.700-5.700l-1 1M14 10a4 4 0 0 0-5.700 0l-3 3a4 4 0 0 0 5.700 5.700l1-1" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/>')))
    items += ('<li><button type="button" class="sh-b sh-native" hidden data-share-url="%s" data-share-title="%s" aria-label="Teilen über das Gerät" title="Teilen">%s<span>Teilen</span></button></li>'
              % (url, title.replace('"', '&quot;'), svg('<circle cx="6" cy="12" r="2.200" fill="currentColor"/><circle cx="17.500" cy="6" r="2.200" fill="currentColor"/><circle cx="17.500" cy="18" r="2.200" fill="currentColor"/><path d="M7.800 11l8-4M7.800 13l8 4" stroke="currentColor" stroke-width="1.6"/>')))
    js = ("<script>(function(){var s=document.currentScript.parentNode,n=s.querySelector('.sh-native'),c=s.querySelector('[data-copy]');"
          "if(navigator.share&&n){n.hidden=false;n.addEventListener('click',function(){navigator.share({title:n.dataset.shareTitle,url:n.dataset.shareUrl}).catch(function(){})})}"
          "c.addEventListener('click',function(){var u=c.dataset.copy,l=c.querySelector('span'),o=l.textContent;"
          "function ok(){l.textContent='Kopiert';setTimeout(function(){l.textContent=o},2000)}"
          "if(navigator.clipboard){navigator.clipboard.writeText(u).then(ok,function(){})}else{var i=document.createElement('input');i.value=u;document.body.appendChild(i);i.select();try{document.execCommand('copy');ok()}catch(e){}i.remove()}})})();</script>")
    return '<div class="share" role="group" aria-label="Artikel teilen"><b>Artikel teilen</b><ul>%s</ul>%s</div>' % (items, js)
SHARE_CSS = ('.share{margin:2.2em 0 1.2em;padding:16px 0;border-top:1px solid var(--line);border-bottom:1px solid var(--line)}.share b{display:block;font-size:12px;text-transform:uppercase;letter-spacing:.08em;color:var(--%s);margin-bottom:10px}'
             '.share ul{list-style:none;margin:0;padding:0;display:flex;flex-wrap:wrap;gap:8px}.share li{margin:0!important}.sh-b{display:inline-flex;align-items:center;gap:7px;font:inherit;font-size:13px;line-height:1;padding:9px 12px;min-height:40px;border:1px solid var(--line);border-radius:999px;background:transparent;color:inherit;text-decoration:none!important;cursor:pointer}'
             '.sh-b:hover{background:var(--%s);border-color:var(--%s)}.sh-b:focus-visible{outline:3px solid #9466e3;outline-offset:2px}.sh-b[hidden]{display:none}@media(max-width:520px){.sh-b span{position:absolute;width:1px;height:1px;overflow:hidden;clip:rect(0,0,0,0)}.sh-b{padding:10px;min-width:44px;justify-content:center}}')
