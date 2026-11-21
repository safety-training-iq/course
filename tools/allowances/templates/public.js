const LOGO = "data:image/png;base64,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";
const FIELDS = ["name","title","grade","stage","due","cert","next","batch"];
const BATCHES = ["الوجبة الأولى","ملحق الوجبة الأولى","الوجبة الثانية","الوجبة الثالثة","الوجبة الرابعة","الوجبة الخامسة","الوجبة السادسة","الوجبة السابعة","الوجبة الثامنة","الوجبة التاسعة","الوجبة العاشرة"];
const batchesOf = d => String(d.batch||"").split("، ").filter(Boolean);
const GRADES = ["أولى","ثانية","ثالثة","رابعة","خامسة","سادسة","سابعة","ثامنة","تاسعة","عاشرة"];
const CERTS = ["دكتوراه","ماجستير","دبلوم عالي","بكالوريوس","دبلوم","اعدادية","متوسطة","ابتدائية","يقرأ ويكتب","بدون مؤهل"];
const DATA = JSON.parse(document.getElementById("emp-data").textContent).map(a => Object.fromEntries(FIELDS.map((k,i)=>[k,a[i]])));

const coll = new Intl.Collator("ar");
const norm = s => String(s||"").replace(/[ً-ْـ]/g,"").replace(/[أإآٱ]/g,"ا").replace(/ة/g,"ه").replace(/ى/g,"ي").replace(/ؤ/g,"و").replace(/ئ/g,"ي").replace(/\s+/g," ").trim();
const esc = s => String(s ?? "").replace(/[&<>"]/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c]));
const $ = id => document.getElementById(id);
const TODAY = new Date(); TODAY.setHours(0,0,0,0);
function parseDate(s){
  const m=/^(\d{1,2})\/(\d{1,2})\/(\d{4})$/.exec(String(s).trim()); if(!m) return null;
  const d=new Date(+m[3],+m[2]-1,+m[1]); return d.getDate()===+m[1]&&d.getMonth()===+m[2]-1?d:null;
}
DATA.forEach(d=>{
  d._n=norm(d.name); d._k=d._n.replace(/ /g,"");
  const dt=parseDate(d.next);
  d.status=!dt?"bad":dt<=TODAY?"due":(dt-TODAY)/864e5<=30?"soon":"later";
});
DATA.sort((a,b)=>coll.compare(a.name,b.name));
const STATUS={due:"مستحقة",soon:"خلال 30 يوماً",later:"قادمة",bad:"يُراجَع التاريخ"};
const state={view:"alpha",limit:150};

$("app").innerHTML=`
<header class="mast wrap">
  <img src="${LOGO}" alt="شعار الفرع">
  <div class="txt">
    <div class="eyebrow">كشف العلاوات السنوية 2026</div>
    <h1>فرع توزيع كهرباء الصدر - قسم الشؤون الإدارية - شعبة الإسناد الإداري - <span class="bolt">مستحقي العلاوات</span></h1>
    <p class="lede">ابحث عن اسمك لتعرف درجتك ومرحلتك وتاريخ علاوتك. الأسماء مرتبة أبجدياً، ويمكنك العزل حسب الدرجة أو الشهادة أو العنوان الوظيفي.</p>
  </div>
</header>
<div class="wrap"><div class="notice" id="notice"></div><div class="stats" id="stats"></div></div>
<div class="bar"><div class="wrap">
  <div class="search">
    <svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="11" cy="11" r="7"/><path d="M20 20l-4-4"/></svg>
    <input id="q" type="search" placeholder="اكتب اسمك أو جزءاً منه…" autocomplete="off" aria-label="بحث بالاسم">
  </div>
  <div class="filters">
    <label for="fGrade">الدرجة<select id="fGrade"></select></label>
    <label for="fCert">الشهادة<select id="fCert"></select></label>
    <label for="fTitle">العنوان الوظيفي<select id="fTitle"></select></label>
    <label for="fStatus">العلاوة<select id="fStatus"></select></label>
  </div>
  <div class="row2">
    <div class="actions">
      <div class="seg" role="group" aria-label="طريقة العرض">
        <button id="vAlpha" aria-pressed="true">أبجدي</button>
        <button id="vGrade" aria-pressed="false">حسب الدرجة</button>
        <button id="vCert" aria-pressed="false">حسب الشهادة</button>
      </div>
      <button class="btn" id="reset">مسح الفلاتر</button>
    </div>
    <div class="count" id="count"></div>
  </div>
</div></div>
<main class="wrap" id="out" aria-live="polite"></main>
<footer class="wrap">
  <div>«المرحلة» هي مرحلتك الحالية، و«المستحقة» هي المرحلة التي تنتقل إليها بالعلاوة. إذا وجدت خطأً في بياناتك فراجع قسم الشؤون الإدارية.</div>
</footer>`;

function countBy(k){const c={};DATA.forEach(d=>c[d[k]]=(c[d[k]]||0)+1);return c;}
function opts(sel,label,values,counts){sel.innerHTML=`<option value="">${label}</option>`+values.map(v=>`<option value="${esc(v)}">${esc(v)} (${counts[v]||0})</option>`).join("");}
const cG=countBy("grade"),cC=countBy("cert"),cT=countBy("title"),cS=countBy("status");
opts($("fGrade"),"كل الدرجات",GRADES.filter(g=>cG[g]),cG);
opts($("fCert"),"كل الشهادات",[...CERTS.filter(c=>cC[c]),...Object.keys(cC).filter(c=>!CERTS.includes(c))],cC);
opts($("fTitle"),"كل العناوين",Object.keys(cT).filter(Boolean).sort(coll.compare),cT);
const cB={}; DATA.forEach(d=>batchesOf(d).forEach(b=>cB[b]=(cB[b]||0)+1));
const BL=Object.keys(cB).sort((a,b)=>(BATCHES.indexOf(a)+99*(BATCHES.indexOf(a)<0))-(BATCHES.indexOf(b)+99*(BATCHES.indexOf(b)<0)));
$("notice").innerHTML=`<b>تنبيه:</b> هذه هي الوجبات المنجزة إلى الآن فقط، وسوف تُضاف بقية الوجبات تدريجياً عند إكمالها. إذا لم تجد اسمك فقد يكون ضمن وجبة لم تُضف بعد.`;
$("fStatus").innerHTML=`<option value="">الكل</option>`+["due","soon","later"].filter(s=>cS[s]).map(s=>`<option value="${s}">${STATUS[s]} (${cS[s]})</option>`).join("");
$("stats").innerHTML=[[DATA.length,"موظفاً"],[Object.keys(cG).length,"درجات"],[Object.keys(cC).length,"شهادات"]]
  .map(([n,l])=>`<div class="stat"><b>${n.toLocaleString("ar")}</b><span>${l}</span></div>`).join("");

function filtered(){
  const q=norm($("q").value),terms=q.split(" ").filter(Boolean),qk=q.replace(/ /g,"");
  const g=$("fGrade").value,c=$("fCert").value,t=$("fTitle").value,s=$("fStatus").value,bt="";
  return {q,rows:DATA.filter(d=>(!g||d.grade===g)&&(!c||d.cert===c)&&(!t||d.title===t)&&(!s||d.status===s)&&(!bt||batchesOf(d).includes(bt))&&
    (!terms.length||terms.every(x=>d._n.includes(x))||d._k.includes(qk)))};
}
function hl(name,q){
  if(!q) return esc(name);
  const chars=[...name];let joined="",map=[];
  chars.forEach((c,i)=>{for(const ch of norm(c)){joined+=ch;map.push(i);}});
  const mark=new Array(chars.length).fill(false);
  q.split(" ").filter(Boolean).forEach(t=>{let i=joined.indexOf(t);while(i>-1){for(let j=i;j<i+t.length;j++)mark[map[j]]=true;i=joined.indexOf(t,i+t.length);}});
  let out="",open=false;
  chars.forEach((c,i)=>{if(mark[i]&&!open){out+="<mark>";open=true}if(!mark[i]&&open){out+="</mark>";open=false}out+=esc(c);});
  return out+(open?"</mark>":"");
}
function rowHTML(d,q){
  return `<div class="emp">
    <div class="nm">${hl(d.name,q)}</div>
    <div class="org">${esc(d.title||"—")}</div>
    <div class="pay"><div class="ln"><span><span class="k">المرحلة</span> ${esc(d.stage)} <span class="arrow">←</span> ${esc(d.due)}</span><span><span class="k">العلاوة</span> ${esc(d.next||"—")}</span></div></div>
    <div class="tags"><span class="tag g">${esc(d.grade)}</span><span class="tag">${esc(d.cert)}</span><span class="pill ${d.status==="bad"?"soon":d.status}">${STATUS[d.status]}</span></div>
  </div>`;
}
const firstLetter=d=>d._n[0]||"#";
function render(){
  const {q,rows}=filtered(),out=$("out");
  $("count").innerHTML=`يظهر <b>${rows.length.toLocaleString("ar")}</b> من ${DATA.length.toLocaleString("ar")}`;
  if(!rows.length){out.innerHTML=`<div class="empty">لا يوجد اسم يطابق هذا البحث. جرّب كتابة الاسم الأول فقط، أو اضغط «مسح الفلاتر».</div>`;return;}
  if(state.view==="alpha"){
    const shown=rows.slice(0,state.limit),per={};rows.forEach(r=>{const L=firstLetter(r);per[L]=(per[L]||0)+1;});
    let html="",cur=null,buf="";
    const flush=()=>{if(cur!==null)html+=`<div class="letter">${esc(cur)}<small>${per[cur]}</small></div><div class="flat">${buf}</div>`;};
    shown.forEach(d=>{const L=firstLetter(d);if(L!==cur){flush();cur=L;buf="";}buf+=rowHTML(d,q);});
    flush();
    if(rows.length>shown.length) html+=`<button class="btn more" id="more">عرض المزيد (${(rows.length-shown.length).toLocaleString("ar")} متبقٍ)</button>`;
    out.innerHTML=html;
    const m=$("more");if(m)m.onclick=()=>{state.limit+=300;render();};
  }else{
    const key=state.view==="grade"?"grade":state.view==="batch"?"batch":"cert",order=key==="grade"?GRADES:key==="batch"?BATCHES:CERTS;
    const groups={};rows.forEach(d=>(key==="batch"?batchesOf(d).filter(v=>!$("fBatch").value||v===$("fBatch").value):[d[key]]).forEach(v=>(groups[v]=groups[v]||[]).push(d)));
    const names=Object.keys(groups).sort((a,b)=>order.indexOf(a)-order.indexOf(b));
    const openAll=names.length===1||!!q;
    out.innerHTML=names.map((n,i)=>`<details class="grp"${openAll?" open":""} data-i="${i}"><summary><span class="lbl">${key==="grade"?"الدرجة ":""}${esc(n||"غير محدد")}</span><span class="n">${groups[n].length}</span></summary><div class="list"></div></details>`).join("");
    out.querySelectorAll("details.grp").forEach(det=>{
      const g=groups[names[+det.dataset.i]];
      const fill=()=>{const box=det.querySelector(".list");if(!box.dataset.done){box.innerHTML=g.map(d=>rowHTML(d,q)).join("");box.dataset.done=1;}};
      if(det.open)fill();det.addEventListener("toggle",()=>det.open&&fill());
    });
  }
}
let tm;$("q").addEventListener("input",()=>{clearTimeout(tm);tm=setTimeout(()=>{state.limit=150;render();},120);});
["fGrade","fCert","fTitle","fStatus"].forEach(id=>$(id).addEventListener("change",()=>{state.limit=150;render();}));
const views={vAlpha:"alpha",vGrade:"grade",vCert:"cert"};
Object.keys(views).forEach(id=>$(id).addEventListener("click",()=>{state.view=views[id];Object.keys(views).forEach(b=>$(b).setAttribute("aria-pressed",b===id));render();}));
$("reset").onclick=()=>{$("q").value="";["fGrade","fCert","fTitle","fStatus"].forEach(id=>$(id).value="");state.limit=150;render();};
render();
