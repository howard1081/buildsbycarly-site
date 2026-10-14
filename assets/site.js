(function(){
var d=document,b=d.body;
// main menu
var mb=d.querySelector('.menu-button'),nav=d.getElementById('site-nav');
function setMenu(open){b.classList.toggle('menu-open',open);mb.setAttribute('aria-expanded',open);mb.querySelector('.menu-label').textContent=open?'Close':'Menu';if(!open)closeSubs()}
if(mb)mb.addEventListener('click',function(){setMenu(mb.getAttribute('aria-expanded')!=='true')});
var subs=[].slice.call(d.querySelectorAll('.has-sub'));
function closeSubs(except){subs.forEach(function(li){if(li!==except){li.classList.remove('open');li.querySelector('button').setAttribute('aria-expanded','false')}})}
subs.forEach(function(li){var bt=li.querySelector('button');bt.addEventListener('click',function(e){e.stopPropagation();var open=!li.classList.contains('open');closeSubs(li);li.classList.toggle('open',open);bt.setAttribute('aria-expanded',open)})});
d.addEventListener('click',function(e){if(!e.target.closest('.has-sub'))closeSubs()});
d.addEventListener('keydown',function(e){if(e.key!=='Escape')return;var o=d.querySelector('.has-sub.open');if(o){closeSubs();o.querySelector('button').focus();return}if(b.classList.contains('menu-open')){setMenu(false);mb.focus()}});
// video on request
d.querySelectorAll('.video').forEach(function(v){var p=v.querySelector('.play');if(!p)return;p.addEventListener('click',function(){var f=d.createElement('iframe');f.src='https://www.youtube-nocookie.com/embed/'+v.dataset.yt+'?autoplay=1&rel=0';f.title=p.getAttribute('aria-label').replace('Play the ','');f.allow='autoplay; encrypted-media; fullscreen';f.allowFullscreen=true;v.innerHTML='';v.appendChild(f);f.focus()})});
// galleries
d.querySelectorAll('[data-open-gallery]').forEach(function(bt){bt.addEventListener('click',function(){var g=d.getElementById(bt.dataset.openGallery);g.classList.add('show-all');bt.remove();var f=g.querySelector('li.extra a');if(f)f.focus()})});
var lb=d.querySelector('.lightbox');
if(lb&&lb.showModal){var img=lb.querySelector('img'),cap=lb.querySelector('figcaption'),items=[],ix=0,opener=null;
function show(i){ix=(i+items.length)%items.length;var a=items[ix],t=a.querySelector('img');img.src=a.href;img.alt=t?t.alt:'';cap.textContent=a.dataset.caption||('Photo '+(ix+1)+' of '+items.length)}
d.querySelectorAll('.gallery').forEach(function(g){g.querySelectorAll('a').forEach(function(a,i){a.addEventListener('click',function(e){e.preventDefault();items=[].slice.call(g.querySelectorAll('a'));opener=a;show(items.indexOf(a));lb.showModal();b.style.overflow='hidden';lb.querySelector('.lb-close').focus()})})});
lb.querySelector('.lb-close').addEventListener('click',function(){lb.close()});
lb.querySelector('.lb-prev').addEventListener('click',function(){show(ix-1)});
lb.querySelector('.lb-next').addEventListener('click',function(){show(ix+1)});
lb.addEventListener('click',function(e){if(e.target===lb)lb.close()});
lb.addEventListener('keydown',function(e){if(e.key==='ArrowLeft')show(ix-1);if(e.key==='ArrowRight')show(ix+1)});
lb.addEventListener('close',function(){b.style.overflow='';if(opener)opener.focus()})}
// preselect model from ?model=
var qm=new URLSearchParams(location.search).get('model');
if(qm){d.querySelectorAll('select[name=model]').forEach(function(s){[].forEach.call(s.options,function(o){if(o.value===qm||o.text===qm)s.value=o.value})});d.querySelectorAll('input[name=model]').forEach(function(c){if(c.value===qm)c.checked=true})}
// forms
function errFor(el){var f=el.closest('.field');return f?f.querySelector('.field-error'):null}
function msg(el){if(el.validity.valueMissing)return el.type==='checkbox'?'Please tick this box to continue.':(el.type==='radio'?'Please choose an option.':'Please fill in this field.');if(el.validity.typeMismatch)return el.type==='email'?'Please enter a valid email address.':'Please check this value.';return 'Please check this field.'}
d.querySelectorAll('.bbc-form').forEach(function(f){var st=f.querySelector('.status'),sub=f.querySelector('[type=submit]'),label=sub.textContent,busy=false;
f.querySelectorAll('input,select,textarea').forEach(function(el){el.addEventListener('input',function(){if(el.getAttribute('aria-invalid')==='true'&&el.checkValidity()){el.removeAttribute('aria-invalid');var er=errFor(el);if(er){er.hidden=true;er.textContent=''}}})});
f.addEventListener('submit',function(e){e.preventDefault();if(busy)return;var bad=[];
f.querySelectorAll('input,select,textarea').forEach(function(el){if(el.name==='_gotcha')return;var er=errFor(el);if(!el.checkValidity()){bad.push(el);el.setAttribute('aria-invalid','true');if(er){er.textContent=msg(el);er.hidden=false;if(el.id)el.setAttribute('aria-describedby',er.id||'')}}else{el.removeAttribute('aria-invalid');if(er){er.hidden=true;er.textContent=''}}});
if(bad.length){st.textContent='Please fix the highlighted fields.';st.className='status err';bad[0].focus();return}
var fd=new FormData(f),data={};fd.forEach(function(v,k){data[k]=data[k]?data[k]+', '+v:v});data.form=f.dataset.form;data.page=location.href;
busy=true;sub.disabled=true;sub.textContent='Sending…';st.textContent='Sending your message…';st.className='status';
fetch(window.BBC_FORM_ENDPOINT,{method:'POST',body:new URLSearchParams(data)}).then(function(r){if(!r.ok)throw 0;return r.text()}).then(function(){f.reset();st.textContent='Thank you. Your message was received and Carly will be in touch. For anything urgent call (865) 505-0514.';st.className='status ok';st.focus&&st.setAttribute('tabindex','-1');st.focus()})
.catch(function(){st.textContent='Sorry, your message did not send. Your answers are still here, so please try again, or call (865) 505-0514 or email info@buildsbycarly.com.';st.className='status err'})
.then(function(){busy=false;sub.disabled=false;sub.textContent=label})})});
})();
