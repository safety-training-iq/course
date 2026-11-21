// Builds a password-protected standalone copy of the admin page.
// Usage: node lock.js <admin.html> <out.html> <password> <forge.min.js>
// The data and app script are AES-256-GCM encrypted (PBKDF2-SHA256 key). The page decrypts with
// WebCrypto when the browser offers it, else with the bundled forge library (in-app web viewers).
const fs = require('fs'), crypto = require('crypto');
const [src, out, pw, forgePath] = process.argv.slice(2);
const t = fs.readFileSync(src, 'utf8');
const css = t.slice(t.indexOf('<style id="app-css">') + 20, t.indexOf('</style>', t.indexOf('<style id="app-css">')));
const di = t.lastIndexOf('\n<script id="emp-data" type="application/json">') + 47;
const data = t.slice(di, t.indexOf('</script>', di));
const ji = t.lastIndexOf('\n<script id="app-js">') + 21;
const js = t.slice(ji, t.lastIndexOf('</script>'));
if (!data.startsWith('{"meta"') || !js.includes('const FIELDS')) throw new Error('unexpected admin page layout');
const salt = crypto.randomBytes(16), iv = crypto.randomBytes(12), ITER = 60000;
const key = crypto.pbkdf2Sync(pw, salt, ITER, 32, 'sha256');
const c = crypto.createCipheriv('aes-256-gcm', key, iv);
const enc = Buffer.concat([c.update(JSON.stringify({ data, js }), 'utf8'), c.final(), c.getAuthTag()]);
const b64 = b => b.toString('base64');
const forge = fs.readFileSync(forgePath, 'utf8');
const html = `<!DOCTYPE html>
<html lang="ar" dir="rtl"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>مستحقي العلاوات - النسخة الشاملة المحمية</title>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=IBM+Plex+Sans+Arabic:wght@400;500;600;700&family=Noto+Kufi+Arabic:wght@600;800&display=swap">
<style id="app-css">${css}</style>
<style>
#lock{min-height:100vh;display:grid;place-items:center;padding:24px 16px}
#lock form{background:var(--surface);border:1px solid var(--line);border-radius:12px;padding:24px;width:min(420px,100%);display:grid;gap:12px;text-align:center}
#lock h1{font-size:20px;margin:0}
#lock p{margin:0;color:var(--muted);font-size:14px}
#lock input{font:inherit;font-size:18px;padding:12px;border:1.5px solid var(--line);border-radius:8px;background:var(--bg);color:var(--ink);text-align:center}
#lock button{font:inherit;font-size:16px;padding:12px;border:0;border-radius:8px;background:var(--navy);color:var(--navy-ink);cursor:pointer}
#lock .err{color:var(--bolt);min-height:1.4em}
</style></head><body>
<div id="lock"><form id="lf">
<h1>مستحقي العلاوات - النسخة الشاملة</h1>
<p>هذه النسخة محمية لأنها تحتوي على الرواتب وأرقام الانتساب. أدخل كلمة السر لفتحها.</p>
<input id="pw" type="password" autocomplete="current-password" placeholder="كلمة السر" aria-label="كلمة السر" required>
<button type="submit">فتح</button>
<div class="err" id="err"></div>
<noscript><p style="color:#c00">هذه الصفحة تحتاج متصفحاً (Chrome أو Safari).</p></noscript>
</form></div>
<div id="app"></div>
<script>${forge}</script>
<script>
const E={s:"${b64(salt)}",i:"${b64(iv)}",n:${ITER},c:"${b64(enc)}"};
const u8=s=>Uint8Array.from(atob(s),c=>c.charCodeAt(0));
document.getElementById("lf").addEventListener("submit",async ev=>{
  ev.preventDefault();const err=document.getElementById("err");
  const pw=document.getElementById("pw").value;
  err.textContent="جارٍ الفتح… قد يستغرق بضع ثوانٍ";
  await new Promise(r=>setTimeout(r,50));
  try{
    let text=null;
    if(window.crypto&&crypto.subtle&&window.isSecureContext!==false){
      try{
        const base=await crypto.subtle.importKey("raw",new TextEncoder().encode(pw),"PBKDF2",false,["deriveKey"]);
        const key=await crypto.subtle.deriveKey({name:"PBKDF2",salt:u8(E.s),iterations:E.n,hash:"SHA-256"},base,{name:"AES-GCM",length:256},false,["decrypt"]);
        text=new TextDecoder().decode(await crypto.subtle.decrypt({name:"AES-GCM",iv:u8(E.i)},key,u8(E.c)));
      }catch(e){ if(e&&e.name==="OperationError") throw e; text=null; }
    }
    if(text==null){
      const f=window.forge, all=atob(E.c), tag=all.slice(-16), body=all.slice(0,-16);
      const key=f.pkcs5.pbkdf2(f.util.encodeUtf8(pw),atob(E.s),E.n,32,f.md.sha256.create());
      const d=f.cipher.createDecipher("AES-GCM",key);
      d.start({iv:atob(E.i),tag:f.util.createBuffer(tag)});
      d.update(f.util.createBuffer(body));
      if(!d.finish()) throw new Error("bad");
      text=f.util.decodeUtf8(d.output.getBytes());
    }
    const p=JSON.parse(text);
    document.getElementById("lock").remove();
    const d=document.createElement("script");d.type="application/json";d.id="emp-data";d.textContent=p.data;document.body.appendChild(d);
    const s=document.createElement("script");s.id="app-js";s.textContent=p.js;document.body.appendChild(s);
  }catch(e){err.textContent="كلمة السر غير صحيحة.";}
});
</script></body></html>`;
fs.writeFileSync(out, html);
console.log('ok', (html.length / 1e6).toFixed(2) + 'MB');
