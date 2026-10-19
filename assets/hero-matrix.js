/* KI Fachblatt: decorative, local signal field. No tracking or network I/O. */
(function(){
'use strict';
var host=document.querySelector('.hero-matrix'),canvas=host&&host.querySelector('canvas');
if(!canvas||!canvas.getContext)return;
var ctx=canvas.getContext('2d');if(!ctx)return;
var reduced=matchMedia('(prefers-reduced-motion: reduce)'),mobile=matchMedia('(max-width: 800px)'),visible=false,raf=0,last=0,phase=0,w=440,h=360,paused=false,button=host.querySelector(".matrix-pause");
function allowed(){return !paused&&visible&&!document.hidden&&!reduced.matches&&!mobile.matches;}
function draw(t){
 ctx.clearRect(0,0,w,h);
 for(var row=0;row<25;row++)for(var col=0;col<31;col++){
  var nx=(col-15)/15,ny=(row-12)/12;
  var edge=Math.max(0,1-Math.pow(Math.abs(nx),4))*Math.max(0,1-Math.pow(Math.abs(ny),4));
  var wave=Math.sin(nx*4.5+phase)*Math.cos(ny*3.2-phase*.5);
  var ridge=Math.exp(-Math.pow(ny-.34*Math.sin(nx*3+phase*.7),2)*10);
  var x=25+col*13+wave*3,y=24+row*13+Math.sin(nx*4+phase)*ridge*13;
  var strength=(.16+.62*ridge)*edge;
  ctx.beginPath();ctx.arc(x,y,.75+ridge*1.65+wave*.2,0,Math.PI*2);ctx.fillStyle='rgba(112,64,205,'+strength.toFixed(3)+')';ctx.fill();
 }
}
function frame(now){
 raf=0;if(!allowed()){host.classList.remove('is-active');return;}
 if(now-last>=33){phase+=Math.min(now-last,80)*.00028;last=now;draw(now);}
 raf=requestAnimationFrame(frame);
}
function sync(){
 if(button)button.hidden=mobile.matches||reduced.matches; 
 if(!allowed()){if(raf)cancelAnimationFrame(raf);raf=0;host.classList.remove('is-active');return;}
 if(!raf){last=performance.now();host.classList.add('is-active');raf=requestAnimationFrame(frame);}
}
function size(){var dpr=Math.min(devicePixelRatio||1,1.5);canvas.width=Math.round(w*dpr);canvas.height=Math.round(h*dpr);ctx.setTransform(dpr,0,0,dpr,0,0);draw(0);sync();}
if(!('IntersectionObserver' in window))return;
new IntersectionObserver(function(entries){visible=entries[0].isIntersecting;sync();},{threshold:.05}).observe(host);
document.addEventListener('visibilitychange',sync);
if(reduced.addEventListener){reduced.addEventListener('change',sync);mobile.addEventListener('change',sync);}
if(button)button.addEventListener('click',function(){paused=!paused;button.setAttribute('aria-pressed',String(paused));button.textContent=paused?'Animation starten':'Animation pausieren';sync();});
window.addEventListener('resize',size,{passive:true});size();
})();
