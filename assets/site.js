(function(){
  var hdr=document.querySelector('.site-header'), tog=document.querySelector('.menu-toggle');
  tog.addEventListener('click',function(){var o=hdr.classList.toggle('open');tog.setAttribute('aria-expanded',o)});
  document.querySelectorAll('.has-sub > button').forEach(function(b){
    b.addEventListener('click',function(e){var li=b.parentElement,o=!li.classList.contains('open');
      document.querySelectorAll('.has-sub.open').forEach(function(x){x.classList.remove('open');x.firstChild.setAttribute('aria-expanded','false')});
      if(o){li.classList.add('open');b.setAttribute('aria-expanded','true')}});
  });
  document.addEventListener('click',function(e){if(!e.target.closest('.has-sub'))document.querySelectorAll('.has-sub.open').forEach(function(x){x.classList.remove('open')})});
  window.addEventListener('scroll',function(){hdr.classList.toggle('scrolled',scrollY>10)},{passive:true});

  document.querySelectorAll('.video').forEach(function(v){v.addEventListener('click',function(){
    v.innerHTML='<iframe src="https://www.youtube.com/embed/'+v.dataset.yt+'?autoplay=1&rel=0" allow="autoplay; encrypted-media; fullscreen" allowfullscreen title="Video tour"></iframe>';})});

  var lb=document.querySelector('.lightbox'),lbImg=lb.querySelector('img'),set=[],idx=0;
  function show(i){idx=(i+set.length)%set.length;lbImg.src=set[idx];}
  document.querySelectorAll('.gallery').forEach(function(g){var links=[].slice.call(g.querySelectorAll('a'));
    links.forEach(function(a,i){a.addEventListener('click',function(e){e.preventDefault();set=links.map(function(x){return x.href});show(i);lb.hidden=false;document.body.style.overflow='hidden'})})});
  function close(){lb.hidden=true;document.body.style.overflow=''}
  lb.querySelector('.lb-close').onclick=close; lb.querySelector('.lb-prev').onclick=function(){show(idx-1)}; lb.querySelector('.lb-next').onclick=function(){show(idx+1)};
  lb.addEventListener('click',function(e){if(e.target===lb)close()});
  document.addEventListener('keydown',function(e){if(lb.hidden)return;if(e.key==='Escape')close();if(e.key==='ArrowLeft')show(idx-1);if(e.key==='ArrowRight')show(idx+1)});

  document.querySelectorAll('.bbc-form').forEach(function(f){f.addEventListener('submit',function(e){
    e.preventDefault(); var st=f.querySelector('.status'), btn=f.querySelector('[type=submit]');
    if(!f.checkValidity()){f.classList.add('tried');st.textContent='Please fill in the required fields.';st.className='status err';return;}
    var fd=new FormData(f), data={};
    fd.forEach(function(v,k){data[k]=data[k]?data[k]+', '+v:v});
    data.form=f.dataset.form; data.page=location.href;
    btn.disabled=true; st.textContent='Sending...'; st.className='status';
    fetch(window.BBC_FORM_ENDPOINT,{method:'POST',body:new URLSearchParams(data)})
      .then(function(r){if(!r.ok)throw 0;f.reset();f.classList.remove('tried');st.textContent='Thank you! Your message was sent. We will be in touch soon.';st.className='status ok'})
      .catch(function(){st.textContent='Sorry, something went wrong. Please call (865) 505-0514 or email info@buildsbycarly.com.';st.className='status err'})
      .finally(function(){btn.disabled=false});
  })});
})();
