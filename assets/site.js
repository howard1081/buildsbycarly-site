(function(){var d=document,b=d.body;d.documentElement.classList.add('js');
var h=d.querySelector('.site-header'),t=d.querySelector('.menu-toggle');
function sc(){h.classList.toggle('scrolled',scrollY>40)}sc();addEventListener('scroll',sc,{passive:true});
t.addEventListener('click',function(){var o=b.classList.toggle('nav-open');t.setAttribute('aria-expanded',o)});
d.querySelectorAll('.has-sub>button').forEach(function(x){x.addEventListener('click',function(){var li=x.parentNode,o=li.classList.toggle('open');x.setAttribute('aria-expanded',o);d.querySelectorAll('.has-sub.open').forEach(function(y){if(y!==li)y.classList.remove('open')})})});
d.addEventListener('click',function(e){if(!e.target.closest('.has-sub'))d.querySelectorAll('.has-sub.open').forEach(function(y){y.classList.remove('open')})});
var rm=matchMedia('(prefers-reduced-motion: reduce)').matches;
function count(el){var raw=el.textContent.trim(),m=raw.match(/^([^\d]*)([\d,]*\.?\d+)(.*)$/);if(!m||rm)return;var pre=m[1],num=parseFloat(m[2].replace(/,/g,'')),suf=m[3],dec=(m[2].split('.')[1]||'').length,com=m[2].indexOf(',')>-1,t0=null;
function f(v){var s=v.toFixed(dec);if(com)s=Number(s).toLocaleString('en-US',{minimumFractionDigits:dec,maximumFractionDigits:dec});return pre+s+suf}
el.style.minWidth=el.offsetWidth+'px';function st(ts){t0=t0||ts;var p=Math.min((ts-t0)/1600,1),e=1-Math.pow(1-p,3);el.textContent=f(num*e);if(p<1)requestAnimationFrame(st);else el.textContent=raw}requestAnimationFrame(st)}
var io='IntersectionObserver'in window?new IntersectionObserver(function(es){es.forEach(function(e){if(e.isIntersecting){e.target.classList.add('in');e.target.querySelectorAll('[data-count]').forEach(count);if(e.target.hasAttribute('data-count'))count(e.target);io.unobserve(e.target)}})},{rootMargin:'0px 0px -8% 0px'}):null;
d.querySelectorAll('.rv').forEach(function(el,i){if(io)io.observe(el);else el.classList.add('in')});
d.querySelectorAll('[data-count]').forEach(function(el){if(!el.closest('.rv')&&io)io.observe(el)});
var rail=d.querySelector('.rail');d.querySelectorAll('.rail-btn').forEach(function(x){x.addEventListener('click',function(){rail.scrollBy({left:(+x.dataset.dir)*rail.querySelector('.model').offsetWidth*1.05,behavior:'smooth'})})});
d.querySelectorAll('.video').forEach(function(v){v.addEventListener('click',function(){v.innerHTML='<iframe src="https://www.youtube.com/embed/'+v.dataset.yt+'?autoplay=1&rel=0" allow="autoplay; encrypted-media; fullscreen" allowfullscreen title="Video tour"></iframe>'},{once:true})});
var lb=d.querySelector('.lightbox'),li=lb.querySelector('img'),items=[],ix=0;
function show(i){ix=(i+items.length)%items.length;li.src=items[ix].href;lb.hidden=false}
d.querySelectorAll('.gallery').forEach(function(g){g.querySelectorAll('a').forEach(function(a){a.addEventListener('click',function(e){e.preventDefault();items=[].slice.call(g.querySelectorAll('a'));show(items.indexOf(a))})})});
lb.querySelector('.lb-close').onclick=function(){lb.hidden=true};lb.querySelector('.lb-prev').onclick=function(){show(ix-1)};lb.querySelector('.lb-next').onclick=function(){show(ix+1)};
lb.addEventListener('click',function(e){if(e.target===lb)lb.hidden=true});
d.addEventListener('keydown',function(e){if(lb.hidden)return;if(e.key==='Escape')lb.hidden=true;if(e.key==='ArrowLeft')show(ix-1);if(e.key==='ArrowRight')show(ix+1)});
d.querySelectorAll('.bbc-form').forEach(function(f){f.addEventListener('submit',function(e){e.preventDefault();var st=f.querySelector('.status');f.classList.add('tried');if(!f.checkValidity()){st.textContent='Please fill in the required fields.';st.className='status err';return}
var fd=new FormData(f),data={};fd.forEach(function(v,k){data[k]=data[k]?data[k]+', '+v:v});data.form=f.dataset.form;data.page=location.href;st.textContent='Sending…';st.className='status';
fetch(window.BBC_FORM_ENDPOINT,{method:'POST',body:new URLSearchParams(data)}).then(function(r){if(!r.ok)throw 0;f.reset();f.classList.remove('tried');st.textContent='Thank you! Your message was sent. We will be in touch soon.';st.className='status ok'}).catch(function(){st.textContent='Sorry, something went wrong. Please call (865) 505-0514 or email info@buildsbycarly.com.';st.className='status err'})})});
})();
