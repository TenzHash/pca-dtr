PAGE = r"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>PCA - DTR System</title>
<style>
:root{--bg:#eef1f5;--card:#fff;--ink:#18222d;--mut:#667585;--line:#dfe5ec;--pri:#1b6b3a;--side:#0f3d22;--bad:#b42318;--warn:#b45309;--hi:rgba(27,107,58,.12)}
@media(prefers-color-scheme:dark){:root:not([data-theme=light]){--bg:#10161d;--card:#18212b;--ink:#e6ebf0;--mut:#93a0ad;--line:#2a3643;--pri:#4cc27a;--side:#08240f;--hi:rgba(76,194,122,.16)}}:root[data-theme=dark]{--bg:#10161d;--card:#18212b;--ink:#e6ebf0;--mut:#93a0ad;--line:#2a3643;--pri:#4cc27a;--side:#08240f;--hi:rgba(76,194,122,.16)}
*{box-sizing:border-box}html,body{height:100%}body{margin:0;font:14px/1.45 system-ui,Segoe UI,Arial,sans-serif;background:var(--bg);color:var(--ink);display:grid;grid-template-columns:210px 1fr;grid-template-rows:56px 1fr;overflow:hidden}
aside{grid-row:1/3;background:var(--side);color:#cfe0ef;display:flex;flex-direction:column;padding:14px 10px}
aside h1{font-size:16px;color:#fff;margin:2px 8px 2px}aside small{margin:0 8px 16px;opacity:.7;font-size:11px}
nav button{display:block;width:100%;text-align:left;background:none;border:0;color:inherit;padding:9px 12px;border-radius:7px;font:inherit;cursor:pointer;margin-bottom:2px}
nav button:hover{background:rgba(255,255,255,.08)}nav button.on{background:rgba(255,255,255,.16);color:#fff;font-weight:600}
header{background:#1b6b3a;color:#fff;border-bottom:3px solid #f2b705;display:flex;align-items:center;gap:10px;padding:0 18px}
header .sp{flex:1}header .hint{color:#d6ecde}header select{background:#fff;color:#111}header .sec{color:#fff;border-color:#fff}header .btn.sec{color:#fff}header b{font-size:15px}
main{overflow:auto;padding:14px}
input,select,textarea{font:inherit;color:inherit;padding:6px 9px;border:1px solid var(--line);border-radius:7px;background:var(--card);max-width:100%}
button,.btn{font:inherit;background:var(--pri);color:#fff;border:0;border-radius:7px;padding:7px 13px;cursor:pointer;text-decoration:none;display:inline-block}
.sec{background:transparent;color:var(--pri);border:1px solid var(--pri)}.sm{padding:2px 9px;font-size:12px}.x{background:none;color:var(--bad);padding:0 6px}
.card{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:16px;margin-bottom:14px;max-width:760px}
.card h2{margin:0 0 10px;font-size:15px}label{display:block;font-size:12px;color:var(--mut);margin:10px 0 3px}.card input:not([type=file]),.card select{width:100%}
.hint{font-size:12px;color:var(--mut)}.empty{text-align:center;margin:80px auto;max-width:420px;color:var(--mut)}.empty h2{color:var(--ink)}
.split{display:grid;grid-template-columns:300px 1fr;gap:14px;height:calc(100vh - 56px - 28px - 118px)}
.list,.pane{background:var(--card);border:1px solid var(--line);border-radius:10px;overflow:hidden;display:flex;flex-direction:column}
.list>input{margin:10px;width:calc(100% - 20px)}.items{overflow:auto;flex:1}
.it{padding:9px 14px;border-top:1px solid var(--line);cursor:pointer;position:relative}.it:hover{background:var(--hi)}.it.on{background:var(--hi);box-shadow:inset 3px 0 var(--pri)}
.it b{display:block;font-size:13px;padding-right:34px}.it span{font-size:12px;color:var(--mut)}
.pill{position:absolute;right:12px;top:10px;font-style:normal;font-size:11px;padding:1px 7px;border-radius:9px;background:rgba(180,83,9,.16);color:var(--warn)}
.pane{overflow:auto}.pane>div{padding:14px 18px}.pane h2{margin:0}.sub{color:var(--mut);font-size:12px}
.stats{display:grid;grid-template-columns:repeat(6,1fr);gap:8px;margin-top:12px}.stat{border:1px solid var(--line);border-radius:8px;padding:7px 10px}
.stat b{display:block;font-size:18px}.stat span{font-size:11px;color:var(--mut);text-transform:uppercase}
.tabs{display:flex;gap:4px;border-bottom:1px solid var(--line);padding:0 18px}.tabs button{background:none;color:var(--mut);border-radius:0;border-bottom:2px solid transparent;padding:10px 14px}
.tabs button.on{color:var(--pri);border-bottom-color:var(--pri);font-weight:600}
table{width:100%;border-collapse:collapse}th,td{padding:6px 8px;border-bottom:1px solid var(--line);text-align:left;white-space:nowrap}th{font-size:11px;color:var(--mut);text-transform:uppercase;position:sticky;top:0;background:var(--card)}
.num{text-align:right}tr.off td{background:rgba(127,127,127,.08);color:var(--mut)}tr.absent td{color:var(--bad)}td.corr{background:rgba(250,204,21,.3);font-weight:600}.flag{color:var(--warn);font-weight:700}
input.t{width:66px;padding:3px 5px}input.why{width:170px;padding:3px 6px}.row{display:flex;gap:8px;flex-wrap:wrap;align-items:end}
#form{max-width:900px;margin:0 auto;background:#fff;color:#111;border:1px solid var(--line);border-radius:6px;padding:16px 22px}
#form .c{text-align:center}#form h3{margin:2px 0;font-size:20px;letter-spacing:.5px}#form .nm{font-weight:700;font-size:15px;border-bottom:1px solid #111;display:inline-block;min-width:60%;padding:2px}
table.g{border:1.5px solid #111;margin-top:10px}table.g th{background:#fff;color:#111;border:1px solid #111;text-align:center;font-size:11px;text-transform:none;position:static;padding:3px}
table.g td{border:1px solid #555;padding:0;height:25px}table.g td.dy{text-align:center;width:36px;font-size:12px}
table.g input{width:100%;height:24px;border:0;border-radius:0;padding:0 5px;background:transparent;color:#111;font-size:13px;text-align:center}
table.g td.rm input{text-align:left}table.g input:focus{outline:2px solid #1f6feb;outline-offset:-2px;background:#eef5ff}
table.g tr.off td{background:#eee}table.g tr.absent input{color:#b42318}table.g td.corr{background:#fff3b0}table.g td.dis{background:#ddd}
#form textarea{width:100%;height:56px;border:1px solid #111;border-radius:0;color:#111;background:#fff;margin-top:8px}
iframe{width:100%;height:calc(100vh - 260px);min-height:560px;border:1px solid var(--line);border-radius:8px;background:#fff}
.cm{position:fixed;display:none;background:var(--card);border:1px solid var(--line);border-radius:8px;box-shadow:0 8px 24px rgba(0,0,0,.35);padding:4px;z-index:20;min-width:210px}
.cm div{padding:6px 12px;cursor:pointer;border-radius:5px}.cm div:hover{background:var(--hi)}.cm hr{border:0;border-top:1px solid var(--line);margin:4px 0}
td.sel{outline:2px solid #1f6feb;outline-offset:-2px;background:#dbeafe!important}table.g td.mg input{text-align:center;font-weight:700}
#ribbon{background:var(--card);border:1px solid var(--line);border-radius:10px;margin-bottom:12px}.rtabs{display:flex;gap:2px;border-bottom:1px solid var(--line);padding:0 10px}
.rtabs button{background:none;color:var(--mut);border-radius:0;border-bottom:2px solid transparent;padding:7px 12px}.rtabs button.on{color:var(--pri);border-bottom-color:var(--pri);font-weight:600}
.rbody{display:flex;gap:10px;flex-wrap:wrap;align-items:end;padding:8px 12px}.rf label{margin:0 0 2px}.rf input,.rf select{padding:4px 7px}
.sgs{display:grid;grid-template-columns:1fr 1fr;gap:30px;margin-top:14px;text-align:center;color:#111}.sg .box{height:66px;border-bottom:1.5px solid #111;display:flex;align-items:flex-end;justify-content:center}
.sg img{max-height:62px;max-width:100%}.sg input{border:0;border-bottom:1px dashed #999;text-align:center;font-weight:700;color:#111;background:transparent;width:80%}
.brand{display:flex;gap:10px;align-items:center;margin:0 6px 18px}.brand b{display:block;color:#fff;font-size:13px;line-height:1.15}.brand small{margin:0!important;color:#f2b705;font-size:10px}
.rg{display:flex;flex-direction:column;border-right:1px solid var(--line);padding:2px 12px}.rg:last-child{border:0}.rgi{display:flex;gap:6px;align-items:center;flex:1;flex-wrap:wrap}.rgl{font-size:11px;color:var(--mut);text-align:center;margin-top:4px}
.rgi button,.rgi select{padding:5px 10px}.rgi input[type=color]{width:34px;height:30px;padding:1px;border:1px solid var(--line);border-radius:5px;background:var(--card)}
table.g th{background:#f3f3f3!important}table.g td.dy{background:#f3f3f3;color:#444}table.g td{border-color:#c9d1d9}
table.g input:focus{outline:2px solid #1b6b3a!important;background:#f1faf4!important}td.sel{outline:2px solid #1b6b3a!important;background:#dff1e5!important}
#md{position:fixed;inset:0;background:rgba(0,0,0,.45);display:none;align-items:center;justify-content:center;z-index:50}
.mb{background:var(--card);color:var(--ink);border-radius:12px;padding:20px 22px;width:440px;max-width:92vw;box-shadow:0 20px 50px rgba(0,0,0,.4);border-top:4px solid #f2b705}
.mb h3{margin:0 0 8px;font-size:16px}.mb p{margin:0 0 12px;color:var(--mut)}.mb input{width:100%;margin-bottom:10px}#mch{display:flex;gap:6px;flex-wrap:wrap;margin-bottom:12px}.mf{display:flex;gap:8px;justify-content:flex-end}
#tip{position:fixed;display:none;background:#1c2630;color:#fff;padding:5px 10px;border-radius:6px;font-size:12px;max-width:290px;z-index:60;pointer-events:none;box-shadow:0 4px 14px rgba(0,0,0,.3)}
#toast{position:fixed;bottom:18px;right:18px;background:var(--side);color:#fff;padding:9px 16px;border-radius:8px;display:none;z-index:9}
@media(max-width:900px){body{grid-template-columns:1fr}aside{display:none}.split{grid-template-columns:1fr;height:auto}.stats{grid-template-columns:repeat(3,1fr)}}
</style></head><body>
<aside><div class="brand"><svg width="38" height="38" viewBox="0 0 34 34"><circle cx="17" cy="17" r="16" fill="#f2b705"/><path d="M17 28V15m0 0c-4-5-9-4-11-2 5-1 8 0 11 2zm0 0c4-5 9-4 11-2-5-1-8 0-11 2zm0 0c-1-5 1-9 4-10-2 3-3 6-4 10zm0 0c1-5-1-9-4-10 2 3 3 6 4 10z" fill="none" stroke="#0f3d22" stroke-width="2" stroke-linecap="round"/></svg><div><b>Philippine Coconut Authority</b><small>DTR System &middot; CSC Form 48</small></div></div>
<nav><button data-v="dtr">Daily Time Records</button><button data-v="files">Files &amp; Roster</button><button data-v="remarks">Leave / Official Business</button><button data-v="audit">Audit Log</button></nav><div id="ver" style="margin-top:auto;padding:8px 12px;font-size:11px;color:#cfe0ef;opacity:.75"></div></aside>
<header><b id="office"></b><span class="hint">Month</span><select id="mo"></select><span class="sp"></span><button class="sm" id="upd" style="display:none;background:#f2b705;color:#111"></button> <button class="sec sm" id="th" title="Switch light / dark mode">Light / Dark</button> <span id="dl"></span></header>
<main id="view"></main><div id="toast"></div><div class="cm" id="cm"></div>
<script>
const $=id=>document.getElementById(id),G=u=>fetch(u).then(r=>r.json()),
J=(u,b)=>fetch(u,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(b)}).then(r=>r.json()),
hm=m=>m?`${Math.floor(m/60)}:${String(m%60).padStart(2,"0")}`:"0:00",
esc=s=>String(s??"").replace(/[&<>"]/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c])),
offName=o=>o==="regional"?"Regional Office":o.replace("-"," ").replace(/\b\w/g,c=>c.toUpperCase())+" Provincial Office";
let S={},V="dtr",ym="",emps=[],hol=[],sel=null,D=null,editing=null,tab="daily",q="";
document.body.insertAdjacentHTML("beforeend",'<div id="md"><div class="mb"><h3 id="mt"></h3><p id="mp"></p><input id="mi"><div id="mch"></div><div class="mf"><button class="sec" id="mc">Cancel</button><button id="mk">OK</button></div></div></div><div id="tip"></div>');
function modal(o){return new Promise(res=>{const M=$("md"),I=$("mi");$("mt").textContent=o.title||"";$("mp").innerHTML=o.body||"";I.style.display=o.input?"block":"none";I.value=o.value||"";
 $("mch").innerHTML=(o.chips||[]).map(c=>`<button class="sm sec" data-c="${esc(c)}">${esc(c)}</button>`).join("");$("mk").textContent=o.ok||"OK";$("mc").style.display=o.cancel===null?"none":"";M.style.display="flex";
 const done=v=>{M.style.display="none";M.onclick=document.onkeydown=null;res(v)};
 $("mk").onclick=()=>done(o.input?I.value.trim():true);$("mc").onclick=()=>done(o.input?null:o.cancel===null);
 M.onclick=e=>{if(e.target===M)$("mc").onclick();const c=e.target.closest("[data-c]");if(c){I.value=c.dataset.c;I.focus()}};
 document.onkeydown=e=>{if(e.key==="Escape")$("mc").onclick();if(e.key==="Enter")$("mk").onclick()};
 setTimeout(()=>o.input?I.focus():$("mk").focus(),30)})}
const ask=(title,body,value,chips)=>modal({title,body,input:1,value,chips}),confirmBox=(title,body,ok)=>modal({title,body,ok}),alertBox=(body,title)=>modal({title:title||"Notice",body,cancel:null});
const TIPS={'[data-m="paste"]':"Paste copied cells (or a block from Excel) starting at the selected cell",'[data-m="cut"]':"Copy the selected cells, then clear them",'[data-m="copy"]':"Copy the selected cells",
 '[data-m="mergesel"]':"Merge the selected time cells (1 to 4) into one cell showing the chosen text",'#mgsel':"Text for the merged cell. Choose Custom to type your own",'[data-m="unmerge"]':"Split merged cells back into separate cells",
 '[data-m="clear"]':"Clear the selected cells","[data-m=revert]":"Undo manual changes on the selected days and restore the biometric times",'[data-m="fill"]':"Give the selected cells the chosen background color (it also prints)",
 '#fillc':"Pick a fill color",'[data-m="nofill"]':"Remove the background color from the selected cells",'#ribbon [data-m="dl"]':"Download this employee's DTR as a PDF",'#ribbon [data-m="print"]':"Print this employee's DTR",
 '[data-rt="tools"]':"Editing tools: clipboard, merge, fill color and output",'[data-rt="settings"]':"Office, print layout, names, overtime and holiday settings",
 '[data-s="office"]':"The office decides which schedule rules apply",'[data-s="layout"]':"Two copies side by side on one page, or one copy per page",'[data-s="operator"]':"Your name, recorded in the audit log with every edit",
 '[data-s="in_charge"]':"Supervisor printed under the In Charge line for staff whose supervisor is not in the roster",'[data-s="division"]':"Division or station printed under the name for staff whose division is not in the roster",'[data-s="ot_threshold"]':"Overtime shorter than this many minutes is ignored",'[data-s="utility"]':"Names of utility workers (7:00-4:00 schedule), separated by commas",
 '[data-s="holidays"]':"Extra holidays as YYYY-MM-DD, separated by commas. Quiet weekdays are also detected automatically",'#th':"Switch between light and dark mode",'#mo':"Choose the month",
 '#dl a[href^="/pdf"]':"One PDF with every employee's DTR for this month",'#dl a[href^="/zip"]':"A ZIP with one PDF per employee",'#dl a[href^="/xlsx"]':"Excel summary of totals and daily details for HR and payroll",
 '#q':"Search employees by name",'#why':"Reason saved in the audit log for the edits you make",'#mnote':"Printed in the Monthly Note box of the DTR",'#s_inch':"Type the In Charge name printed under the signature line",
 '[data-g="up"]':"Upload a PNG or JPG signature to print above the name. Leave blank to sign by hand",'[data-g="rm"]':"Remove the signature image (the line prints blank)",'[data-a="print"]':"Print this DTR",
 'a[href*="download=1"]':"Download this employee's DTR as a PDF",'#pl':"Choose how the DTR is laid out on the page",'#grid input[data-f^="am"],#grid input[data-f^="pm"]':"Time in 24-hour format, e.g. 08:05 (blank clears)",
 '#grid input[data-f="ut_h"],#grid input[data-f="ut_m"]':"Undertime hours or minutes (overrides the computed value)",'#grid input[data-f="ot"]':"Overtime as h:mm or minutes",'#grid input[data-f="remark"]':"Remarks printed on the DTR",
 '#grid input[data-f="span"]':"Merged cell text. Clear it to unmerge",'[data-a="radd"]':"Add this remark to the chosen dates",'[data-a="gadd"]':"Add this remark for every employee",
 '.tabs [data-t="daily"]':"Edit the Form 48 like a spreadsheet",'.tabs [data-t="form"]':"See exactly what will print, and choose the layout",'.tabs [data-t="leave"]':"Record leave, OB or travel for one or more dates",
 'nav [data-v="dtr"]':"Review and edit employees' DTRs",'nav [data-v="files"]':"Add attendance files, back up, restore and update",'nav [data-v="remarks"]':"Remarks for leave, OB, holidays and suspensions",'nav [data-v="audit"]':"Every manual edit: who, when, old and new value, reason",
 '#rbtn':"Load a backup file made on this or another PC",'#ucheck':"Look for a newer version",'#upd':"A newer version is available"};
const TH={Day:"Day of the month",Arrival:"Time arrived",Departure:"Time left",Hours:"Undertime hours",Minutes:"Undertime minutes",Overtime:"Time worked past the latest official out-time",Remarks:"Notes such as NO TIME-OUT or Leave","A.M.":"Morning","P.M.":"Afternoon",Undertime:"Late arrival + early departure + extra lunch"};
const STAT={Present:"Days with at least one punch",Absent:"Working days with no punch and no remark",Late:"Days arrived after the allowed time",Undertime:"Total undertime this month",Overtime:"Total overtime this month","To review":"Days with incomplete punches or manual changes"};
let tt=null;function applyTips(){for(const k in TIPS)document.querySelectorAll(k).forEach(e=>{if(!e.dataset.tip)e.dataset.tip=TIPS[k]});
 document.querySelectorAll("#form th").forEach(e=>{const t=TH[e.textContent.trim()];if(t&&!e.dataset.tip)e.dataset.tip=t});document.querySelectorAll(".stat").forEach(e=>{const t=STAT[e.textContent.replace(/[\d:.]/g,"").trim()];if(t&&!e.dataset.tip)e.dataset.tip=t})}
new MutationObserver(()=>{clearTimeout(tt);tt=setTimeout(applyTips,60)}).observe(document.body,{childList:true,subtree:true});
let tw=null;document.addEventListener("mouseover",e=>{const el=e.target.closest("[data-tip]");clearTimeout(tw);$("tip").style.display="none";if(!el)return;tw=setTimeout(()=>{const t=$("tip"),r=el.getBoundingClientRect();t.textContent=el.dataset.tip;t.style.display="block";
 t.style.left=Math.max(6,Math.min(r.left,innerWidth-t.offsetWidth-8))+"px";t.style.top=(r.bottom+6+t.offsetHeight>innerHeight?r.top-t.offsetHeight-6:r.bottom+6)+"px"},450)});
document.addEventListener("mousedown",()=>{clearTimeout(tw);$("tip").style.display="none"});
function toast(t){const e=$("toast");e.textContent=t;e.style.display="block";setTimeout(()=>e.style.display="none",2500)}
async function boot(){S=await G("/api/state");if(!S.months.includes(ym))ym=S.months[S.months.length-1]||"";await loadMonth();go(V)}
async function loadMonth(){emps=[];hol=[];if(ym){const d=await G("/api/month/"+ym);emps=d.employees;hol=d.holidays}
 if(sel&&!emps.find(e=>e.key===sel))sel=null;D=sel?await G(`/api/employee/${ym}/${sel}`):null}
function go(v){V=v;document.querySelectorAll("nav button").forEach(b=>b.classList.toggle("on",b.dataset.v===v));render()}
function render(){const s=S.settings;$("ver").textContent="Version "+(S.version||"older");document.documentElement.dataset.theme=s.theme||"";$("office").textContent=offName(s.office);
 $("mo").innerHTML=S.months.map(m=>`<option ${m===ym?"selected":""}>${m}</option>`).join("");
 $("dl").innerHTML=ym&&V==="dtr"?`<a class="btn" href="/pdf/${ym}">All DTRs (PDF)</a> <a class="btn sec" href="/zip/${ym}">Individual PDFs (ZIP)</a> <a class="btn sec" href="/xlsx/${ym}">HR summary (Excel)</a>`:"";
 ({dtr:vDtr,files:vFiles,remarks:vRem,audit:vAud,settings:vSet})[V]()}
$("mo").onchange=async e=>{ym=e.target.value;sel=null;editing=null;await loadMonth();render()};
document.querySelector("nav").onclick=e=>{const b=e.target.closest("button");if(b)go(b.dataset.v)};
/* ---------- DTR view ---------- */
function vDtr(){if(!S.files.length)return $("view").innerHTML=`<div class="empty"><h2>No attendance files yet</h2><p>Add the ZKTeco exports to start generating DTRs, or restore a backup from another PC.</p><button onclick="go('files')">Add files</button> <button class="sec" onclick="go('files')">Restore a backup</button></div>`;
 $("view").innerHTML=`${ribbon()}<div class="split"><div class="list"><input id="q" placeholder="Search employee" value="${esc(q)}"><div class="items" id="items"></div></div><div class="pane" id="pane"></div></div>`;
 $("q").oninput=e=>{q=e.target.value;items()};items();pane();bindRibbon()}
function items(){$("items").innerHTML=emps.filter(e=>e.name.toLowerCase().includes(q.toLowerCase())).map(e=>`<div class="it ${sel===e.key?"on":""}" data-k="${e.key}"><b>${esc(e.name)}</b><span>${e.id_no?`ID ${esc(e.id_no)} · `:""}${e.days_present} days · UT ${hm(e.ut)} · OT ${hm(e.ot)}</span>${e.review?`<i class="pill">${e.review}</i>`:""}</div>`).join("")||'<p class="hint" style="padding:14px">No match.</p>'}
function pane(){if(!D)return $("pane").innerHTML=`<div class="empty" style="margin:60px auto"><h2>Select an employee</h2><p>Pick a name on the left to review the month, edit times and preview the Form 48.${hol.length?`<br><br>No-work days detected: ${hol.join(", ")}`:""}</p></div>`;
 const e=emps.find(x=>x.key===sel);
 const body=tab==="daily"?daily():tab==="form"?preview():leave();
 $("pane").innerHTML=`<div><h2>${esc(D.name)}</h2><div class="sub">${D.sched} schedule · ${esc(D.office_label||"")}${D.division?" · "+esc(D.division):""}${D.supervisor?" · Supervisor: "+esc(D.supervisor):""}</div>
 <div class="row" style="margin-top:8px"><a class="btn" href="/pdf/${ym}/${sel}?download=1&layout=${PLv()}">Download this DTR (PDF)</a><button class="sec" data-a="print">Print this DTR</button></div>
 <div class="stats" id="stats">${[["Present",e.days_present],["Absent",e.absences],["Late",e.late_count],["Undertime",hm(e.ut)],["Overtime",hm(e.ot)],["To review",e.review]].map(([a,b])=>`<div class="stat"><b>${b}</b><span>${a}</span></div>`).join("")}</div></div>
 <div class="tabs">${[["daily","Form 48 (editable)"],["form","Print preview"],["leave","Leave / OB"]].map(([k,t])=>`<button data-t="${k}" class="${tab===k?"on":""}">${t}</button>`).join("")}</div><div>${body}</div>`;if(tab==="daily")bindGrid()}
const COLS=["am_in","am_out","pm_in","pm_out","ut_h","ut_m","ot","remark"];
const cellVal=(r,f)=>f==="ut_h"?(r.ut>=60?Math.floor(r.ut/60):""):f==="ut_m"?(r.ut%60||""):f==="ot"?(r.ot?hm(r.ot):""):f==="remark"?(r.spans.some(s=>s[3])?"":r.note||(["saturday","sunday","holiday","absent"].includes(r.kind)?r.kind.toUpperCase():"")):r[f];
const cellOv=(r,f)=>r.ov.includes(f.startsWith("ut")?"ut":f);
let SEL=null,drag=false,CLIP="",rt="tools",PL=null;
const PLv=()=>PL||S.settings.layout||"two";
function preview(){return `<div class="row" style="margin-bottom:10px"><div><label>Print layout</label><select id="pl"><option value="two" ${PLv()==="two"?"selected":""}>Two copies side by side</option><option value="one" ${PLv()==="one"?"selected":""}>One copy per page</option></select></div><button data-a="print">Print</button><a class="btn sec" href="/pdf/${ym}/${sel}?download=1&layout=${PLv()}">Download PDF</a></div><iframe src="/pdf/${ym}/${sel}?layout=${PLv()}&t=${Date.now()}#toolbar=0&view=FitH"></iframe>`}
function daily(){const by={};D.rows.forEach(r=>by[+r.date.slice(8)]=r);const e=emps.find(x=>x.key===sel),nd=new Date(+ym.slice(0,4),+ym.slice(5),0).getDate();let rows="";
 for(let d=1;d<=31;d++){const r=by[d];if(!r){rows+=`<tr><td class="dy">${d<=nd?d:""}</td>${COLS.map(()=>'<td class="dis"></td>').join("")}</tr>`;continue}
  const off=["saturday","sunday","holiday"].includes(r.kind),mg=r.kind==="remark",inp=(f,c,v)=>`<input data-r="${d-1}" data-c="${c}" data-f="${f}" data-d="${r.date}" value="${esc(v)}">`;
  let cells="";const fl=r.fill||{},st=c=>fl[c]?` style="background:${fl[c]}"`:"";
  for(let c=0;c<8;c++){const sp=c<4?r.spans.find(x=>x[0]===c):null;
   if(sp){cells+=`<td colspan="${sp[1]-sp[0]+1}" class="mg ${r.ov.includes("merge")||sp[3]?"corr":""}"${st(c)}>${inp(sp[3]?"remark":"span",c,sp[2])}</td>`;c=sp[1];continue}
   const f=COLS[c];cells+=`<td class="${f==="remark"?"rm ":""}${cellOv(r,f)?"corr":""}"${st(c)}>${inp(f,c,cellVal(r,f))}</td>`}
  rows+=`<tr class="${off?"off":r.kind==="absent"?"absent":""}"><td class="dy">${d}</td>${cells}</tr>`}
 const sg=(w,has,key)=>`<div class="sg"><div class="box">${has?`<img src="/sig/${w}/${key}?t=${Date.now()}">`:'<span class="hint">blank - sign by hand</span>'}</div><div><b>${w==="emp"?esc(D.name):(D.sup_roster?esc(D.supervisor):`<input id="s_inch" value="${esc(S.settings.in_charge)}" placeholder="Supervisor name">`)}</b></div><div class="hint">${w==="emp"?"(Signature over printed name)":"(In Charge)"}</div><div class="row" style="justify-content:center;margin-top:4px"><button class="sm sec" data-g="up" data-w="${w}" data-k="${key}">Upload image</button>${has?`<button class="sm x" data-g="rm" data-w="${w}" data-k="${key}">Remove</button>`:""}</div></div>`;
 return `<div class="row" style="margin-bottom:10px"><div><label>Reason recorded for edits</label><input id="why" value="Manual edit" style="width:240px"></div><span class="hint" style="max-width:560px">Edit like a spreadsheet: type, arrows/Enter/Tab, Esc to undo, drag to select, paste from Excel. <b>Right-click</b> for Merge (Leave/OB), Copy, Cut, Paste, Clear and Revert. Times are 24-hour. Every edit is logged.</span></div>
 <div id="form"><div class="c"><small>Civil Service Form No. 48</small><h3>DAILY TIME RECORD</h3><div class="nm">${esc(D.name)}</div><div class="hint">(Name)${D.id_no?` &middot; ID No. ${esc(D.id_no)}`:""}${D.division?` &middot; ${esc(D.division)}`:""}</div><div style="margin-top:6px"><b>For the month of ${new Date(+ym.slice(0,4),+ym.slice(5)-1,1).toLocaleString("en",{month:"long"}).toUpperCase()} ${ym.slice(0,4)}</b></div></div>
 <table class="g"><thead><tr><th rowspan="2">Day</th><th colspan="2">A.M.</th><th colspan="2">P.M.</th><th colspan="2">Undertime</th><th rowspan="2">Overtime</th><th rowspan="2">Remarks</th></tr><tr><th>Arrival</th><th>Departure</th><th>Arrival</th><th>Departure</th><th>Hours</th><th>Minutes</th></tr></thead><tbody id="grid">${rows}</tbody>
 <tfoot><tr><td class="dy"><b>TOTAL</b></td><td colspan="4"></td><td colspan="2" class="c" id="tut"><b>${hm(e.ut)}</b></td><td class="c" id="tot"><b>${hm(e.ot)}</b></td><td></td></tr></tfoot></table>
 <label style="color:#111"><b>MONTHLY NOTE</b></label><textarea id="mnote" placeholder="Notes printed in the Monthly Note box">${esc(D.note)}</textarea>
 <div class="sgs">${sg("emp",D.sig_emp,sel)}${sg("incharge",D.sig_inc,"x")}</div></div>`}
function parseOT(v){v=v.trim();if(!v)return 0;const m=v.match(/^(\d+):([0-5]\d)$/);return m?+m[1]*60+ +m[2]:Math.round(+v)}
function toCell(inp,v){const f=inp.dataset.f,date=inp.dataset.d,row=D.rows.find(x=>x.date===date);
 if(f==="ut_h"||f==="ut_m"){const h=f==="ut_h"?(+v||0):Math.floor(row.ut/60),m=f==="ut_m"?(+v||0):row.ut%60;return{date,field:"ut",value:String(h*60+m)}}
 if(f==="ot"){const n=parseOT(v);if(isNaN(n))throw Error("Overtime: use h:mm (e.g. 1:30) or minutes.");return{date,field:"ot",value:String(n)}}
 if(f==="span"){const c=+inp.dataset.c;return{date,field:"merge",value:serSp(row.spans.filter(s=>!s[3]).map(s=>s[0]===c?[s[0],s[1],v.replace(/[|]/g," ").trim()]:s).filter(s=>s[2]))}}
 return{date,field:f,value:v}}
const serSp=a=>a.sort((x,y)=>x[0]-y[0]).map(s=>`${s[0]}-${s[1]}:${s[2]}`).join("|"),serFl=m=>Object.keys(m).sort().map(k=>`${k}:${m[k]}`).join(",");
async function sendCells(cells){const r=await J("/api/cells",{ym,key:sel,reason:($("why")||{}).value||"Manual edit",cells});if(r.error)toast(r.error);await loadMonth();
 if(cells.some(c=>["remark","merge","fill"].includes(c.field)))pane();else syncGrid();return r}
function syncGrid(){if(!D||tab!=="daily")return;D.rows.forEach(r=>COLS.forEach(f=>{const i=document.querySelector(`#grid input[data-d="${r.date}"][data-f="${f}"]`);if(!i)return;
 if(document.activeElement!==i)i.value=f==="remark"&&r.kind==="remark"?r.note:cellVal(r,f);i.dataset.orig=i.value;i.parentElement.classList.toggle("corr",cellOv(r,f))}));
 const e=emps.find(x=>x.key===sel);if($("tut")){$("tut").innerHTML=`<b>${hm(e.ut)}</b>`;$("tot").innerHTML=`<b>${hm(e.ot)}</b>`}
 $("stats").innerHTML=[["Present",e.days_present],["Absent",e.absences],["Late",e.late_count],["Undertime",hm(e.ut)],["Overtime",hm(e.ot)],["To review",e.review]].map(([a,b])=>`<div class="stat"><b>${b}</b><span>${a}</span></div>`).join("");items()}
function selInputs(){if(!SEL)return[];const [r1,r2]=[SEL.r1,SEL.r2].sort((a,b)=>a-b),[c1,c2]=[SEL.c1,SEL.c2].sort((a,b)=>a-b);
 return[...document.querySelectorAll("#grid input")].filter(i=>+i.dataset.r>=r1&&+i.dataset.r<=r2&&+i.dataset.c>=c1&&+i.dataset.c<=c2)}
function paintSel(){document.querySelectorAll("#grid td.sel").forEach(t=>t.classList.remove("sel"));const a=selInputs();if(a.length>1)a.forEach(i=>i.parentElement.classList.add("sel"))}
async function pasteAt(r0,c0,t){const cells=[];try{t.replace(/\r/g,"").replace(/\n$/,"").split("\n").forEach((ln,dr)=>ln.split("\t").forEach((v,dc)=>{const n=$("grid").querySelector(`input[data-r="${r0+dr}"][data-c="${c0+dc}"]`);if(n)cells.push(toCell(n,v.trim()))}));await sendCells(cells);toast("Pasted "+cells.length+" cells")}catch(x){toast(x.message)}}
function selRect(){const [r1,r2]=[SEL.r1,SEL.r2].sort((a,b)=>a-b),[c1,c2]=[SEL.c1,SEL.c2].sort((a,b)=>a-b);return{r1,r2,c1,c2}}
async function doAct(m){const ins=selInputs();if(!ins.length)return toast("Click or drag to select cells first");const rows=[...new Set(ins.map(i=>i.dataset.d))],R=selRect();
 if(m==="dl")return location.href=`/pdf/${ym}/${sel}?download=1&layout=${PLv()}`;
 if(m==="copy"||m==="cut"){const g={};ins.forEach(i=>(g[i.dataset.r]=g[i.dataset.r]||[]).push([+i.dataset.c,i.value]));CLIP=Object.keys(g).sort((a,b)=>a-b).map(k=>g[k].sort((a,b)=>a[0]-b[0]).map(x=>x[1]).join("\t")).join("\n");
  if(navigator.clipboard)navigator.clipboard.writeText(CLIP).catch(()=>{});toast("Copied");if(m==="copy")return}
 if(m==="clear"||m==="cut"){try{return await sendCells(ins.map(i=>toCell(i,"")))}catch(x){return toast(x.message)}}
 if(m==="paste"){let t=CLIP;try{t=await navigator.clipboard.readText()}catch(x){}return pasteAt(+ins[0].dataset.r,+ins[0].dataset.c,t||"")}
 if(m==="revert"){for(const d of rows)await J("/api/correct/revert",{ym,key:sel,date:d,reason:""});await loadMonth();pane();return toast("Restored")}
 const rowOf=d=>D.rows.find(x=>x.date===d);
 if(m==="unmerge"){const cells=rows.map(d=>({date:d,field:"merge",value:serSp(rowOf(d).spans.filter(s=>!s[3]&&(s[1]<R.c1||s[0]>R.c2)))}));await sendCells(cells);return toast("Unmerged")}
 if(m==="fill"||m==="nofill"){const col=m==="fill"?$("fillc").value:null;const cells=rows.map(d=>{const mp={...(rowOf(d).fill||{})};for(let c=R.c1;c<=Math.min(R.c2,7);c++)col?mp[c]=col:delete mp[c];return{date:d,field:"fill",value:serFl(mp)}});await sendCells(cells);return toast(col?"Filled":"Fill removed")}
 if(m.startsWith("merge:")){let t=m.slice(6);if(t==="*")t=(await ask("Merge cells","Type the text to show in the merged cells, or pick one:","",["LEAVE","OFFICIAL BUSINESS","OB","TRAVEL ORDER","WORK FROM HOME","SICK LEAVE","VACATION LEAVE","HOLIDAY"]))||"";if(!t)return;t=t.replace(/[|]/g," ").toUpperCase();
  const a=R.c1,b=Math.min(R.c2,3);if(a>3)return toast("Merge works on the four time cells (AM/PM Arrival and Departure).");const cells=[];
  rows.forEach(d=>{const sp=rowOf(d).spans.filter(s=>!s[3]&&(s[1]<a||s[0]>b));sp.push([a,b,t]);for(let i=a;i<=b;i++)cells.push({date:d,field:COLS[i],value:""});cells.push({date:d,field:"merge",value:serSp(sp)})});
  await sendCells(cells);toast("Merged "+(b-a+1)+" cell"+(b>a?"s":""))}}
const MENU=[["copy","Copy"],["cut","Cut"],["paste","Paste"],["clear","Clear"],0,["merge:LEAVE","Merge selected cells as LEAVE"],["merge:OFFICIAL BUSINESS","Merge as OFFICIAL BUSINESS"],["merge:TRAVEL ORDER","Merge as TRAVEL ORDER"],["merge:*","Merge with custom text..."],["unmerge","Unmerge"],0,["fill","Fill with ribbon color"],["nofill","Remove fill"],0,["revert","Revert day to biometric"]];
function ribbon(){const s=S.settings,f=(l,h)=>`<div class="rf"><label>${l}</label>${h}</div>`,B=(m,t)=>`<button class="sm sec" data-m="${m}">${t}</button>`,G=(t,h)=>`<div class="rg"><div class="rgi">${h}</div><div class="rgl">${t}</div></div>`;
 const set=[f("Office (for staff not in roster)",`<select data-s="office">${S.offices.map(o=>`<option value="${o}" ${o===s.office?"selected":""}>${offName(o)}</option>`).join("")}</select>`),f("Print layout",`<select data-s="layout"><option value="two" ${s.layout!=="one"?"selected":""}>2 copies / page</option><option value="one" ${s.layout==="one"?"selected":""}>1 copy / page</option></select>`),f("Your name",`<input data-s="operator" value="${esc(s.operator)}">`),f("Name of supervisor (In Charge)",`<input data-s="in_charge" value="${esc(s.in_charge)}" placeholder="used when the roster has none">`),f("Name of division / station",`<input data-s="division" value="${esc(s.division||"")}" placeholder="used when the roster has none">`),f("Ignore OT under (min)",`<input data-s="ot_threshold" type="number" min="0" value="${s.ot_threshold}" style="width:70px">`),f("Utility workers",`<input data-s="utility" value="${esc(s.utility)}" placeholder="names, comma-separated">`),f("Extra holidays",`<input data-s="holidays" value="${esc(s.holidays.join(", "))}" placeholder="YYYY-MM-DD, ...">`)].join("");
 const home=G("Clipboard",B("paste","Paste")+B("cut","Cut")+B("copy","Copy"))+G("Merge (1-4 cells)",`<select id="mgsel">${["LEAVE","OFFICIAL BUSINESS","TRAVEL ORDER","WORK FROM HOME","SICK LEAVE","VACATION LEAVE","*"].map(x=>`<option value="${x}">${x==="*"?"Custom text...":x}</option>`).join("")}</select><button class="sm" data-m="mergesel">Merge</button>`+B("unmerge","Unmerge"))+G("Cells",B("clear","Clear")+B("revert","Revert day"))+G("Fill color",`<input type="color" id="fillc" value="#ffe699"><button class="sm" data-m="fill">Fill</button>`+B("nofill","No fill"))+G("Output",B("dl","Download PDF")+B("print","Print"));
 return `<div id="ribbon"><div class="rtabs"><button data-rt="tools" class="${rt==="tools"?"on":""}">Home</button><button data-rt="settings" class="${rt==="settings"?"on":""}">Settings</button></div><div class="rbody" style="padding:6px 8px">${rt==="settings"?set:home}</div></div>`}
function bindRibbon(){const R=$("ribbon");if(!R)return;R.querySelectorAll("[data-rt]").forEach(b=>b.onclick=()=>{rt=b.dataset.rt;R.outerHTML=ribbon();bindRibbon()});
 R.querySelectorAll("[data-m]").forEach(b=>{b.onmousedown=e=>e.preventDefault();b.onclick=()=>{const m=b.dataset.m;if(m==="print")return document.querySelector('button[data-a="print"]').click();doAct(m==="mergesel"?"merge:"+$("mgsel").value:m)}});
 R.querySelectorAll("[data-s]").forEach(i=>i.onchange=async()=>{const p={};R.querySelectorAll("[data-s]").forEach(x=>{const k=x.dataset.s;p[k]=k==="holidays"?x.value.split(",").map(y=>y.trim()).filter(Boolean):k==="ot_threshold"?+x.value||0:x.value});await J("/api/settings",p);await boot();toast("Saved")})}
function bindGrid(){const g=$("grid");g.querySelectorAll("input").forEach(i=>i.dataset.orig=i.value);
 g.addEventListener("focusin",e=>e.target.select&&e.target.select());
 g.addEventListener("change",async e=>{try{await sendCells([toCell(e.target,e.target.value)])}catch(x){toast(x.message);e.target.value=e.target.dataset.orig}});
 g.addEventListener("mousedown",e=>{const i=e.target.closest("td")&&e.target.closest("td").querySelector("input");if(!i||e.button)return;const r=+i.dataset.r,c=+i.dataset.c;
  if(e.shiftKey&&SEL){SEL.r2=r;SEL.c2=c}else SEL={r1:r,c1:c,r2:r,c2:c};drag=true;paintSel()});
 g.addEventListener("mouseover",e=>{if(!drag)return;const i=e.target.closest("td")&&e.target.closest("td").querySelector("input");if(!i)return;SEL.r2=+i.dataset.r;SEL.c2=+i.dataset.c;paintSel();getSelection().removeAllRanges()});
 document.addEventListener("mouseup",()=>drag=false);
 g.addEventListener("contextmenu",e=>{const i=e.target.closest("td")&&e.target.closest("td").querySelector("input");if(!i)return;e.preventDefault();
  if(!selInputs().includes(i)){SEL={r1:+i.dataset.r,c1:+i.dataset.c,r2:+i.dataset.r,c2:+i.dataset.c};paintSel()}
  const m=$("cm");m.innerHTML=MENU.map(x=>x?`<div data-m="${x[0]}">${x[1]}</div>`:"<hr>").join("");m.style.display="block";m.style.left=Math.min(e.clientX,innerWidth-230)+"px";m.style.top=Math.min(e.clientY,innerHeight-330)+"px"});
 g.addEventListener("keydown",e=>{const i=e.target,r=+i.dataset.r,c=+i.dataset.c,go=(rr,cc)=>{const n=g.querySelector(`input[data-r="${rr}"][data-c="${cc}"]`);if(n){e.preventDefault();n.focus()}};
  if(e.key==="Escape"){i.value=i.dataset.orig;i.select()}else if(e.key==="Enter"||e.key==="ArrowDown")go(r+1,c);else if(e.key==="ArrowUp")go(r-1,c);
  else if(e.key==="ArrowRight"&&i.selectionStart===i.value.length)go(r,c+1);else if(e.key==="ArrowLeft"&&i.selectionStart===0)go(r,c-1)});
 g.addEventListener("paste",e=>{const t=e.clipboardData.getData("text");if(!/[\t\n]/.test(t.trim()))return;e.preventDefault();pasteAt(+e.target.dataset.r,+e.target.dataset.c,t)});
 $("mnote").onchange=async e=>{await sendCells([{field:"month_note",value:e.target.value}])};
 if($("s_inch"))$("s_inch").onchange=async e=>{S.settings.in_charge=e.target.value;await J("/api/settings",{in_charge:e.target.value});toast("Saved")};
 $("form").addEventListener("click",async e=>{const b=e.target.closest("button[data-g]");if(!b)return;const k=b.dataset.w==="emp"?sel:"x";
  if(b.dataset.g==="rm"){await J("/api/signature/delete",{kind:b.dataset.w,key:k});await loadMonth();return pane()}
  const f=document.createElement("input");f.type="file";f.accept=".png,.jpg,.jpeg";f.onchange=async()=>{const fd=new FormData();fd.append("kind",b.dataset.w);fd.append("key",k);fd.append("file",f.files[0]);
   const r=await (await fetch("/api/signature",{method:"POST",body:fd})).json();if(r.error)return toast(r.error);await loadMonth();pane();toast("Signature saved")};f.click()})}
function leave(){const mine=S.remarks.map((r,i)=>[r,i]).filter(([r])=>r.employee===sel);
 return `<div class="row"><div><label>From</label><input type="date" id="rs"></div><div><label>To (optional)</label><input type="date" id="re"></div><div><label>Remark</label><select id="rt">${["LEAVE","SICK LEAVE","VACATION LEAVE","OFFICIAL BUSINESS","TRAVEL ORDER","WORK FROM HOME"].map(x=>`<option>${x}</option>`).join("")}</select></div><button data-a="radd">Add</button></div>
 <p class="hint">Days without punches print this remark instead of ABSENT.</p>${mine.length?`<table>${mine.map(([r,i])=>`<tr><td>${esc(r.date)}</td><td>${esc(r.remark)}</td><td><button class="x" data-r="${i}">remove</button></td></tr>`).join("")}</table>`:""}`}
/* ---------- other views ---------- */
function vFiles(){$("view").innerHTML=`<div class="card"><h2>Attendance files</h2><p class="hint">Add the ZKTeco exports (.xls or .xlsx) exactly as they come off the device.</p><input type="file" id="att" multiple accept=".xls,.xlsx">
 <table style="margin-top:10px">${S.files.map(f=>`<tr><td>${esc(f)}</td><td><button class="x" data-f="${esc(f)}">remove</button></td></tr>`).join("")||'<tr><td class="hint">No files yet.</td></tr>'}</table></div>
 <div class="card"><h2>HR roster (optional)</h2><p class="hint">Gives each person's full name, office, schedule and ID number (from the REMARKS text and an optional ID NO. column). ${S.roster?"<b>Roster loaded.</b>":"No roster loaded."}</p><input type="file" id="ros" accept=".xlsx"></div>
 <div class="card"><h2>Backup &amp; restore</h2><p class="hint">A backup holds your attendance files, roster, remarks, edits, signatures and settings. A copy is also saved automatically every day. Use Restore to move everything to another PC.</p>
 <div class="row"><a class="btn" href="/backup">Back up now</a><button class="sec" id="rbtn">Restore from backup...</button></div></div>
 <div class="card"><h2>Program updates</h2><p class="hint">Check whether a newer version of this program is available. Your data stays safe during an update.</p>
 <p>Version in use: <b>${S.version||"older version"}</b></p><div class="row"><button id="ucheck">Check for updates</button><button id="uins" style="display:none;background:#f2b705;color:#111">Install update now</button></div><p id="ures" class="hint" style="margin-top:8px"></p>
 <details style="margin-top:10px"><summary class="hint" style="cursor:pointer">Administrator options</summary><label>Where updates are downloaded from (leave empty to use the setting built into the installer)</label>
 <input id="usrc" value="${esc(S.settings.update_source||"")}" placeholder="Folder or web address provided by your administrator"></details></div>`;
 $("rbtn").onclick=()=>{const f=document.createElement("input");f.type="file";f.accept=".zip";f.onchange=async()=>{if(!await confirmBox("Restore backup","Restoring replaces the data on this PC with the backup. A safety copy of the current data is kept first.","Restore"))return;const fd=new FormData();fd.append("file",f.files[0]);const r=await (await fetch("/api/restore",{method:"POST",body:fd})).json();if(r.error)return alertBox(r.error);await boot();toast("Backup restored")};f.click()};
 $("usrc").onchange=async e=>{await J("/api/settings",{update_source:e.target.value.trim()});S.settings.update_source=e.target.value.trim()};
 $("ucheck").onclick=async()=>{await J("/api/settings",{update_source:$("usrc").value.trim()});S.settings.update_source=$("usrc").value.trim();await checkUpdate(true)};
 $("att").onchange=()=>up($("att"),"attendance");$("ros").onchange=()=>up($("ros"),"roster")}
async function up(el,kind){const f=new FormData();[...el.files].forEach(x=>f.append("files",x));f.append("kind",kind);toast("Reading files...");await fetch("/api/upload",{method:"POST",body:f});await boot();toast("Files loaded")}
function vRem(){$("view").innerHTML=`<div class="card"><h2>For everyone (holiday / suspension)</h2><div class="row"><div><label>From</label><input type="date" id="gs"></div><div><label>To (optional)</label><input type="date" id="ge"></div><div><label>Remark</label><input id="gt" placeholder="e.g. NINOY AQUINO DAY"></div><button data-a="gadd">Add</button></div></div>
 <div class="card"><h2>All remarks</h2><p class="hint">Add leave or official business for one person from their record (Leave / OB tab).</p><table>${S.remarks.map((r,i)=>`<tr><td>${r.employee==="*"?"Everyone":esc((emps.find(e=>e.key===r.employee)||{}).name||r.employee)}</td><td>${esc(r.date)}</td><td>${esc(r.remark)}</td><td><button class="x" data-r="${i}">remove</button></td></tr>`).join("")||'<tr><td class="hint">None yet.</td></tr>'}</table></div>`}
async function vAud(){$("view").innerHTML=`<div class="card" style="max-width:none"><div class="row"><h2 style="flex:1">Correction audit log</h2><a class="btn sec" href="/audit.csv">Download CSV</a></div><div id="al" class="hint">Loading...</div></div>`;
 const a=await G("/api/audit?ym=&key=");$("al").innerHTML=a.length?`<table><thead><tr><th>When</th><th>By</th><th>Employee</th><th>Date</th><th>Field</th><th>From</th><th>To</th><th>Reason</th></tr></thead><tbody>${a.map(x=>`<tr><td>${x.timestamp.replace("T"," ")}</td><td>${esc(x.operator)}</td><td>${esc(x.employee)}</td><td>${x.date}</td><td>${x.field.replace("_"," ")}</td><td>${x.old||"-"}</td><td>${x.new==="__REVERT__"?"(reverted)":x.new||"(cleared)"}</td><td>${esc(x.reason)}</td></tr>`).join("")}</tbody></table>`:"No manual corrections yet."}
function vSet(){const s=S.settings;$("view").innerHTML=`<div class="card"><h2>Settings</h2>
 <label>Office (sets the schedule rules)</label><select id="s_office">${S.offices.map(o=>`<option value="${o}" ${o===s.office?"selected":""}>${offName(o)}</option>`).join("")}</select>
 <label>Your name (recorded on every correction)</label><input id="s_operator" value="${esc(s.operator)}">
 <label>"In Charge" name printed on the DTR</label><input id="s_in_charge" value="${esc(s.in_charge)}">
 <label>Print layout</label><select id="s_layout"><option value="two" ${s.layout!=="one"?"selected":""}>Two copies side by side (default)</option><option value="one" ${s.layout==="one"?"selected":""}>One copy per page</option></select>
 <label>Ignore overtime shorter than (minutes)</label><input id="s_ot" type="number" min="0" value="${s.ot_threshold}">
 <label>Utility workers (names, comma-separated)</label><input id="s_utility" value="${esc(s.utility)}" placeholder="e.g. Dela Cruz, Santos">
 <label>Extra holidays (YYYY-MM-DD, comma-separated)</label><input id="s_holidays" value="${esc(s.holidays.join(", "))}">
 <p class="hint">Holidays are also detected automatically when nobody punched on a weekday. Changes save automatically.</p></div>`;
 document.querySelectorAll("#view input,#view select").forEach(i=>i.onchange=async()=>{await J("/api/settings",{office:$("s_office").value,operator:$("s_operator").value,layout:$("s_layout").value,in_charge:$("s_in_charge").value,ot_threshold:+$("s_ot").value||0,utility:$("s_utility").value,holidays:$("s_holidays").value.split(",").map(x=>x.trim()).filter(Boolean)});await boot();toast("Saved")})}
/* ---------- actions ---------- */
document.addEventListener("click",async e=>{
 const it=e.target.closest(".it");if(it){sel=it.dataset.k;editing=null;D=await G(`/api/employee/${ym}/${sel}`);items();return pane()}
 const tb=e.target.closest(".tabs button");if(tb){tab=tb.dataset.t;return pane()}
 const b=e.target.closest("button[data-a],button[data-r],button[data-f]");if(!b)return;const a=b.dataset.a;
 if(b.dataset.f){await J("/api/delete_file",{name:b.dataset.f});sel=null;return boot()}
 if(b.dataset.r!==undefined){await J("/api/remarks/delete",{index:+b.dataset.r});await boot();return toast("Removed")}
 if(a==="radd"){if(!$("rs").value)return alertBox("Pick the date first.");await J("/api/remarks",{employee:sel,start:$("rs").value,end:$("re").value,remark:$("rt").value});await boot();return toast("Remark added")}
 if(a==="gadd"){if(!$("gs").value||!$("gt").value.trim())return alertBox("Enter the date and remark.");await J("/api/remarks",{employee:"*",start:$("gs").value,end:$("ge").value,remark:$("gt").value});await boot();return toast("Added for everyone")}
 if(a==="print"){const f=document.createElement("iframe");f.style.cssText="position:fixed;width:0;height:0;border:0";f.src=`/pdf/${ym}/${sel}?layout=${PLv()}`;f.onload=()=>{try{f.contentWindow.focus();f.contentWindow.print()}catch(x){toast("Use Download, then print the PDF")}};document.body.appendChild(f);setTimeout(()=>f.remove(),60000);return}
 if(a==="revert"){await J("/api/correct/revert",{ym,key:sel,date:b.dataset.d,reason:""});await loadMonth();pane();toast("Restored biometric values")}
});
document.addEventListener("click",e=>{const m=$("cm");if(m.style.display==="block"){m.style.display="none";const it=e.target.closest("#cm div");if(it)doAct(it.dataset.m)}});
document.addEventListener("change",e=>{if(e.target.id==="pl"){PL=e.target.value;pane()}});
$("th").onclick=async()=>{const dark=getComputedStyle(document.body).backgroundColor.replace(/\D+/g," ").trim().split(" ")[0]<100;const t=dark?"light":"dark";document.documentElement.dataset.theme=t;S.settings.theme=t;await J("/api/settings",{theme:t})};
async function installUpdate(r){if(!await confirmBox("Install update","Install version "+r.latest+" now? The program will close and reopen by itself. Your data is kept.","Install"))return;const x=await J("/api/update/install",{});if(x.error)alertBox(x.error)}
async function checkUpdate(show){const r=await G("/api/update/check"),b=$("upd"),msg=t=>{if($("ures"))$("ures").textContent=t};
 if(r.available){b.style.display="inline-block";b.textContent="Update available - install";b.onclick=()=>installUpdate(r);msg("A new version ("+r.latest+") is available.");if($("uins")){$("uins").style.display="inline-block";$("uins").onclick=()=>installUpdate(r)}}
 else if(show){if($("ures"))$("ures").title=r.error||"";msg(r.code===404?"No update has been published yet, or the update location is not available. Please contact your administrator.":r.error?"Could not reach the update location. Check the network connection and try again.":r.configured?"You are up to date.":"Automatic updates are not set up on this PC. Please contact your administrator.")}}
boot().then(()=>checkUpdate(false));
</script></body></html>"""
