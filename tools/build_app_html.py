"""Turn the Sketch Sprout preview page into the offline page the Android app loads.

Usage: python3 tools/build_app_html.py <preview.html> app/src/main/assets/index.html
"""
import sys

src, out = sys.argv[1], sys.argv[2]
h = open(src, encoding="utf-8").read()


def rep(a, b, count=1):
    global h
    n = h.count(a)
    if n != count:
        raise SystemExit(f"expected {count} of {a[:70]!r}, found {n}")
    h = h.replace(a, b)


def cut(start, end):
    """Remove from start marker up to (not including) end marker."""
    global h
    a = h.index(start)
    b = h.index(end, a)
    h = h[:a] + h[b:]


# Head: drop preview-only bits and the web font links (fonts are bundled).
rep("<title>Sketch Sprout Preview</title>\n", "")
rep('<meta name="claude:viewport-fit-sides" content="cover">\n', "")
rep('<link rel="preconnect" href="https://fonts.googleapis.com">\n', "")
for line in h.splitlines():
    if "fonts.googleapis.com/css2" in line:
        rep(line + "\n", "")
        break

# Body: drop the preview header, jump bar and right-hand desk.
cut('<header class="top">', '<div class="stage">')
cut('<div class="jump"', '<div class="device">')
cut('<div class="desk">', '<svg width="0" height="0"')
h = h.replace('<svg width="0" height="0"', '</div></div>\n<svg width="0" height="0"', 1)

# "My art" tab opens the gallery instead of a toast.
rep('<button type="button" data-soon="My art keeps photos of her paper drawings in a little gallery.">',
    '<button type="button" data-go="art">')
rep("""<div class="sec"><h3>More lessons</h3><small>All 35 are ready</small></div>
              <div class="more"><span>Send Claude a new picture any time <i>· it becomes a lesson</i></span></div>""", "")

ART_VIEW = """
          <!-- MY ART -->
          <section class="view" id="v-art" hidden>
            <div class="drawtop">
              <button class="iconbtn" type="button" data-go="home" aria-label="Back home"><svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round"><path d="M15 5l-7 7 7 7"/></svg></button>
              <h2 class="app-display" style="margin:0;font-size:22px;flex:1">My art</h2>
              <span class="pill"><span id="artCount">0</span></span>
            </div>
            <div class="scroll" style="padding-top:6px">
              <p style="margin:0;font-weight:700;color:var(--a-soft);font-size:14px">Photos of your paper drawings. Add one when you finish a lesson.</p>
              <div class="agrid" id="agrid"></div>
            </div>
            <div class="artview" id="artView" hidden role="dialog" aria-label="My drawing">
              <div class="avtop">
                <button class="avbtn" type="button" id="avClose" aria-label="Close"><svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.6" stroke-linecap="round"><path d="M6 6l12 12M18 6L6 18"/></svg></button>
                <div class="avcap"><b id="avName"></b><span id="avDate"></span></div>
                <span class="avnum" id="avNum"></span>
              </div>
              <div class="avstage">
                <button class="avbtn avnav" type="button" id="avPrev" aria-label="Previous drawing"><svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round"><path d="M15 5l-7 7 7 7"/></svg></button>
                <img id="avImg" alt="">
                <button class="avbtn avnav" type="button" id="avNext" aria-label="Next drawing"><svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round"><path d="M9 5l7 7-7 7"/></svg></button>
              </div>
              <div class="avfoot">
                <div class="avref"><div id="avRef"></div><span>The pencil's</span></div>
                <button class="avdel" type="button" id="avDel">Remove</button>
              </div>
            </div>
          </section>
"""
rep("          <!-- STICKERS -->", ART_VIEW + "\n          <!-- STICKERS -->")
rep('<div class="sgrid" id="sgrid"></div>',
    '<div class="sgrid" id="sgrid"></div>\n              <div class="resetbox"><button class="resetbtn" type="button" id="resetStickers">Reset stickers</button><small id="resetNote">Starts all 35 lessons fresh. Photos in My art are kept.</small></div>')

# Script: remove the preview's change-request box code.
a = h.index("/* ---------- change requests (shared db) ---------- */")
b = h.rindex("})();\n\n</script>")
h = h[:a] + "/*APP_JS*/\n" + h[b:]

rep("t.textContent=msg+' (In the full app.)';", "t.textContent=msg;")
rep("const VIEWS=['home','watch','done','stickers'];", "const VIEWS=['home','watch','done','stickers','art'];")
rep("  if(v==='stickers') renderStickers();", "  if(v==='stickers') renderStickers();\n  if(v==='art') renderArt();\n  if(v!=='art') closeArt();\n  if(v==='home') refreshHome();")
rep("const unlocked=new Set();", "const unlocked=new Set(store.get('done',[]));")
rep("function finished(){ unlocked.add(lessonId); $('starCount').textContent=String(14+unlocked.size*3); go('done'); }",
    "function finished(){ unlocked.add(lessonId); store.set('done',[...unlocked]); $('starCount').textContent=String(unlocked.size*3); go('done'); }")
rep("""  let img=ph.querySelector('img'); if(!img){img=document.createElement('img');img.alt='Photo of her drawing';ph.appendChild(img);} img.src=url;});""",
    """  let img=ph.querySelector('img'); if(!img){img=document.createElement('img');img.alt='Photo of her drawing';ph.appendChild(img);} img.src=url;
  saveArt(url);});""")
rep("""<span class="pill"><span id="stickCount">0</span>/9</span>""",
    """<span class="pill"><span id="stickCount">0</span>/<span id="stickTotal">35</span></span>""")

APP_JS = r"""
/* ---------- app: saved progress, today's pick, my art, back button ---------- */
function refreshHome(){
  $('starCount').textContent=String(unlocked.size*3);
  const next=ORDER.find(id=>!unlocked.has(id))||ORDER[0], N=LESSONS[next];
  putFinal($('todayThumb'),N);
  const today=document.querySelector('.today');
  today.querySelector('h3').textContent=N.name;
  today.querySelector('p').textContent=N.steps.length+' steps · coloured pencils · '+N.mins+' min';
  today.querySelector('[data-lesson]').dataset.lesson=next;
  grid.querySelectorAll('.card[data-lesson]').forEach(c=>c.classList.toggle('done',unlocked.has(c.dataset.lesson)));
}
$('stickTotal').textContent=String(ORDER.length);
function loadArt(){ return store.get('art',[]); }
function saveArt(url){
  const img=new Image();
  img.onload=()=>{
    const s=Math.min(1,900/Math.max(img.width,img.height));
    const c=document.createElement('canvas'); c.width=Math.round(img.width*s); c.height=Math.round(img.height*s);
    c.getContext('2d').drawImage(img,0,0,c.width,c.height);
    const art=loadArt(); art.unshift({lesson:lessonId,name:(L&&L.name)||'',date:new Date().toISOString(),data:c.toDataURL('image/jpeg',.8)});
    while(art.length){ if(store.set('art',art)) break; art.pop(); }
    soon('Saved to My art');
  };
  img.src=url;
}
function renderArt(){
  const art=loadArt(), g=$('agrid'); g.innerHTML='';
  $('artCount').textContent=String(art.length);
  if(!art.length){ g.innerHTML='<p class="empty">No photos yet. Finish a drawing, then tap "Add a photo of my paper".</p>'; return; }
  art.forEach((a,i)=>{
    const fig=document.createElement('figure'); fig.className='artcard';
    const im=document.createElement('img'); im.src=a.data; im.alt=a.name?('My '+a.name):'My drawing';
    const cap=document.createElement('figcaption');
    cap.textContent=(a.name||'Drawing')+' · '+new Date(a.date).toLocaleDateString();
    const open=document.createElement('button'); open.type='button'; open.className='artopen'; open.setAttribute('aria-label','Open '+(a.name||'drawing'));
    open.addEventListener('click',()=>openArt(i));
    fig.append(im,cap,open); g.appendChild(fig);
  });
}
let artIdx=-1, delArm=false;
function openArt(i){
  const art=loadArt(); if(!art.length){ closeArt(); return; }
  artIdx=Math.max(0,Math.min(i,art.length-1)); const a=art[artIdx];
  $('avImg').src=a.data; $('avImg').alt=a.name?('My '+a.name):'My drawing';
  $('avName').textContent=a.name||'My drawing';
  $('avDate').textContent=new Date(a.date).toLocaleDateString(undefined,{day:'numeric',month:'long',year:'numeric'});
  $('avNum').textContent=(artIdx+1)+' / '+art.length;
  $('avPrev').disabled=artIdx===0; $('avNext').disabled=artIdx===art.length-1;
  const les=LESSONS[a.lesson]; const ref=$('avRef'); ref.innerHTML=''; $('avRef').parentElement.hidden=!les;
  if(les) putFinal(ref,les);
  delArm=false; $('avDel').textContent='Remove'; $('avDel').classList.remove('armed');
  $('artView').hidden=false;
}
function closeArt(){ $('artView').hidden=true; artIdx=-1; }
$('avClose').addEventListener('click',closeArt);
$('avPrev').addEventListener('click',()=>openArt(artIdx-1));
$('avNext').addEventListener('click',()=>openArt(artIdx+1));
$('avDel').addEventListener('click',()=>{
  if(!delArm){ delArm=true; $('avDel').textContent='Tap again to remove'; $('avDel').classList.add('armed'); return; }
  const all=loadArt(); all.splice(artIdx,1); store.set('art',all); renderArt();
  if(all.length) openArt(Math.min(artIdx,all.length-1)); else closeArt();
});
(()=>{ let x0=null; const st=document.querySelector('.avstage');
  st.addEventListener('touchstart',e=>{x0=e.touches[0].clientX;},{passive:true});
  st.addEventListener('touchend',e=>{ if(x0==null) return; const dx=e.changedTouches[0].clientX-x0; x0=null;
    if(dx<-50) openArt(artIdx+1); else if(dx>50) openArt(artIdx-1); },{passive:true}); })();
$('screen').appendChild($('homeToast'));
let resetArm=false, resetT=null;
$('resetStickers').addEventListener('click',()=>{
  const b=$('resetStickers');
  if(!resetArm){ resetArm=true; b.textContent='Tap again to reset'; b.classList.add('armed');
    clearTimeout(resetT); resetT=setTimeout(()=>{ resetArm=false; b.textContent='Reset stickers'; b.classList.remove('armed'); },4000); return; }
  clearTimeout(resetT); resetArm=false; b.textContent='Reset stickers'; b.classList.remove('armed');
  unlocked.clear(); store.set('done',[]); renderStickers(); refreshHome(); soon('Stickers reset. Ready for a fresh start!');
});
window.appBack=function(){
  if(!$('artView').hidden){ closeArt(); return true; }
  if(!$('bigPeek').hidden){ $('bigPeek').hidden=true; return true; }
  if(current==='home') return false;
  go('home'); return true;
};
refreshHome();

/* ---------- device test mode: walks every lesson step and asks the test runner for a screenshot ---------- */
if(location.hash==='#autotest'){
  const sleep=ms=>new Promise(r=>setTimeout(r,ms));
  const shot=async name=>{ await sleep(250); console.log('SSHOT:'+name); await sleep(1600); };
  const until=async (fn,ms)=>{ const t0=Date.now(); while(!fn()){ if(Date.now()-t0>ms) return false; await sleep(100);} return true; };
  (async()=>{
    try{ localStorage.clear(); }catch(e){}
    unlocked.clear(); refreshHome();
    await sleep(3000);
    await shot('000_home');
    const sc=document.querySelector('#v-home .scroll');
    for(let k=1;k<=6;k++){ sc.scrollTop=k*sc.clientHeight*0.9; await shot('001_home_scroll'+k); }
    sc.scrollTop=0;
    speed=3;
    for(let n=0;n<ORDER.length;n++){
      const id=ORDER[n], les=LESSONS[id], pre=String(n+1).padStart(2,'0')+'_'+id;
      openLesson(id);
      for(let i=0;i<les.steps.length;i++){
        if(i>0) $('next').click();
        const ok=await until(()=>$('nowTry').classList.contains('show'),60000);
        await shot(pre+'_s'+String(i+1).padStart(2,'0')+(ok?'':'_TIMEOUT'));
      }
      $('peekBtn').click(); await shot(pre+'_zfinal'); $('bigPeek').click();
      if(n===0){ $('next').click(); await sleep(1500); await shot('002_done'); }
      else { unlocked.add(id); store.set('done',[...unlocked]); }
    }
    go('home'); await shot('003_home_after');
    go('stickers'); await shot('004_stickers');
    go('art'); await shot('005_art');
    console.log('SSHOT:END');
  })();
}
"""
rep("/*APP_JS*/\n", APP_JS)

# Storage helper must exist before `unlocked` is created, so put it at the top of the script.
STORE_JS = r"""
const store={
  get(k,d){ try{ const v=localStorage.getItem('ss.'+k); return v?JSON.parse(v):d; }catch(e){ return d; } },
  set(k,v){ try{ localStorage.setItem('ss.'+k,JSON.stringify(v)); return true; }catch(e){ return false; } }
};
"""
rep("const $=id=>document.getElementById(id);", "const $=id=>document.getElementById(id);" + STORE_JS)

FONTS = "\n".join(
    f"@font-face{{font-family:'{fam}';font-weight:{w};font-style:normal;font-display:swap;src:url(fonts/{fam.lower()}-{w}.woff2) format('woff2')}}"
    for fam in ("Grandstander", "Nunito") for w in (500, 600, 700, 800)
)

APP_CSS = """
html,body{height:100%;margin:0;padding:0!important;background:var(--a-paper,#FFFDF8);overscroll-behavior:none}
body{-webkit-tap-highlight-color:transparent;user-select:none;-webkit-user-select:none}
.wrap,.stage{display:block!important;max-width:none!important;margin:0!important;padding:0!important}
.device{max-width:none!important;width:100%!important;padding:0!important;border-radius:0!important;box-shadow:none!important;background:none!important}
.screen{aspect-ratio:auto!important;height:100vh;height:100dvh;border-radius:0!important;max-width:760px;margin:0 auto}
@media (min-width:600px){.grid{grid-template-columns:repeat(3,1fr)!important}.sgrid{grid-template-columns:repeat(4,1fr)!important}}
.card{position:relative}
.card.done::after{content:"\\2713";position:absolute;top:12px;right:12px;width:26px;height:26px;border-radius:50%;background:#3BB273;color:#fff;font:800 15px/26px var(--body);text-align:center;box-shadow:0 2px 6px rgba(0,0,0,.15)}
.agrid{display:grid;grid-template-columns:repeat(2,1fr);gap:12px}
.artcard{margin:0;background:#fff;border:2px solid var(--a-line);border-radius:16px;padding:8px;display:flex;flex-direction:column;gap:6px}
.artcard img{width:100%;aspect-ratio:1;object-fit:cover;border-radius:10px;background:#F4F1EA}
.artcard figcaption{font:700 12px var(--body);color:var(--a-soft)}
.htoast{z-index:40}
.resetbox{display:flex;flex-direction:column;align-items:center;gap:6px;padding:18px 0 8px;text-align:center}
.resetbtn{border:2px solid var(--a-line);background:#fff;color:#C0392B;font:800 14px var(--body);border-radius:999px;padding:10px 18px;cursor:pointer}
.resetbtn.armed{background:#C0392B;border-color:#C0392B;color:#fff}
.resetbox small{font:700 12px var(--body);color:var(--a-soft)}
.artcard{position:relative}
.artopen{position:absolute;inset:0;border:0;background:none;cursor:pointer;border-radius:16px}
.artview{position:absolute;inset:0;z-index:30;background:#1F1E2E;color:#fff;display:flex;flex-direction:column;padding:12px 12px 16px;gap:10px}
.artview[hidden]{display:none!important}
.avtop{display:flex;align-items:center;gap:10px}
.avcap{flex:1;display:flex;flex-direction:column;line-height:1.25}
.avcap b{font:800 18px var(--display)}
.avcap span{font:700 13px var(--body);opacity:.75}
.avnum{font:800 13px var(--body);opacity:.75}
.avbtn{width:44px;height:44px;border-radius:50%;border:0;background:rgba(255,255,255,.12);color:#fff;display:grid;place-items:center;cursor:pointer;flex:none}
.avbtn:disabled{opacity:.25}
.avstage{flex:1;min-height:0;display:flex;align-items:center;gap:8px}
.avstage img{flex:1;min-width:0;max-height:100%;object-fit:contain;border-radius:12px;background:#2B2A3D;align-self:stretch}
.avfoot{display:flex;align-items:center;gap:12px}
.avref{display:flex;align-items:center;gap:8px;flex:1;font:700 13px var(--body);opacity:.9}
.avref>div{width:64px;height:64px;border-radius:10px;background:#FFFDF8;overflow:hidden;flex:none}
.avref>div svg{width:100%;height:100%}
.avdel{border:0;border-radius:999px;background:rgba(255,255,255,.12);color:#FFB4A8;font:800 14px var(--body);padding:10px 16px;cursor:pointer}
.avdel.armed{background:#C0392B;color:#fff}
.empty{grid-column:1/-1;font-weight:700;color:var(--a-soft);text-align:center;padding:24px 8px}
"""

head = (
    '<!doctype html><html lang="en" data-theme="light"><head><meta charset="utf-8">'
    '<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover,user-scalable=no">'
    "<title>Sketch Draw</title><style>" + FONTS + "</style></head><body>\n"
)
# Append the app CSS after the page's first stylesheet.
i = h.index("</style>")
h = h[:i] + APP_CSS + h[i:]

open(out, "w", encoding="utf-8").write(head + h + "\n</body></html>\n")
print("wrote", out, len(head + h), "bytes")
