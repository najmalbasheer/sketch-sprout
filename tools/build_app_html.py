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
          </section>
"""
rep("          <!-- STICKERS -->", ART_VIEW + "\n          <!-- STICKERS -->")

# Script: remove the preview's change-request box code.
a = h.index("/* ---------- change requests (shared db) ---------- */")
b = h.rindex("})();\n\n</script>")
h = h[:a] + "/*APP_JS*/\n" + h[b:]

rep("t.textContent=msg+' (In the full app.)';", "t.textContent=msg;")
rep("const VIEWS=['home','watch','done','stickers'];", "const VIEWS=['home','watch','done','stickers','art'];")
rep("  if(v==='stickers') renderStickers();", "  if(v==='stickers') renderStickers();\n  if(v==='art') renderArt();\n  if(v==='home') refreshHome();")
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
    const del=document.createElement('button'); del.type='button'; del.className='artdel'; del.textContent='Remove'; del.setAttribute('aria-label','Remove this photo');
    del.addEventListener('click',()=>{ if(!confirm('Remove this photo?')) return; const all=loadArt(); all.splice(i,1); store.set('art',all); renderArt(); });
    fig.append(im,cap,del); g.appendChild(fig);
  });
}
window.appBack=function(){
  if(!$('bigPeek').hidden){ $('bigPeek').hidden=true; return true; }
  if(current==='home') return false;
  go('home'); return true;
};
refreshHome();
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
.artdel{align-self:flex-start;border:0;background:none;color:#C0392B;font:800 12px var(--body);padding:2px 0;cursor:pointer}
.empty{grid-column:1/-1;font-weight:700;color:var(--a-soft);text-align:center;padding:24px 8px}
"""

head = (
    '<!doctype html><html lang="en" data-theme="light"><head><meta charset="utf-8">'
    '<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover,user-scalable=no">'
    "<title>Sketch Sprout</title><style>" + FONTS + "</style></head><body>\n"
)
# Append the app CSS after the page's first stylesheet.
i = h.index("</style>")
h = h[:i] + APP_CSS + h[i:]

open(out, "w", encoding="utf-8").write(head + h + "\n</body></html>\n")
print("wrote", out, len(head + h), "bytes")
