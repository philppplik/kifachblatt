(function(){
var bar=document.getElementById('bar');
function p(){var h=document.documentElement;var s=h.scrollTop/(h.scrollHeight-h.clientHeight||1);bar.style.width=(s*100)+'%'}
addEventListener('scroll',p,{passive:true});p();
var io=new IntersectionObserver(function(es){es.forEach(function(e){if(e.isIntersecting){e.target.classList.add('in');io.unobserve(e.target)}})},{threshold:.12});
document.querySelectorAll('.rv').forEach(function(el){io.observe(el)});
var links=[].slice.call(document.querySelectorAll('.toc a'));
if(links.length){var so=new IntersectionObserver(function(es){es.forEach(function(e){if(e.isIntersecting){links.forEach(function(l){l.classList.toggle('on',l.getAttribute('href')==='#'+e.target.id)})}})},{rootMargin:'-20% 0px -70% 0px'});
document.querySelectorAll('.body h2').forEach(function(h){so.observe(h)})}
})();
