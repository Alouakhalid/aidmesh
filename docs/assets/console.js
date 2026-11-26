/* Agent console: renders live status, tool calls, inputs and outputs
   from the recorded real run (docs/data/run.json). */
(async()=>{
const el=document.querySelector('.console[data-agent]');
if(!el)return;
const key=el.dataset.agent;
const CFG={
 verification:{name:'VERIFICATION ANALYST',tools:['credibility_score'],note:'detect_language runs in the LangChain intake step before this agent',input:'reports'},
 triage:{name:'TRIAGE LEAD',tools:['geocode_place','weather_flood_risk'],input:'incidents'},
 dispatch:{name:'RESOURCE DISPATCHER',tools:['nearest_resources','geocode_place','weather_flood_risk'],input:'incidents'},
 communication:{name:'COMMUNITY COMMUNICATOR',tools:[],note:'no external tools: writes from the dispatch plan',input:'dispatch'}
}[key];
const esc=s=>String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;');
const D=await fetch('data/run.json').then(r=>r.json());
const tc=D.meta.tool_calls||{};
let inRows=[];
if(CFG.input==='reports'){
  inRows=D.reports.slice(0,3).map(r=>`<li><b>${esc(r.id)}</b> [${esc(r.source)}] ${esc(r.text.slice(0,72))}${r.text.length>72?'…':''}</li>`);
  inRows.push(`<li>+${D.reports.length-3} more raw reports</li>`);
}else if(CFG.input==='incidents'){
  inRows=D.incidents.slice(0,3).map(i=>`<li><b>${esc(i.report_id)}</b> ${esc(i.need)} · ${esc(i.location)}${i.life_threatening?' · <span class="cnt">LIFE-THREATENING</span>':''}</li>`);
  inRows.push(`<li>+${D.incidents.length-3} more incidents</li>`);
}else{
  inRows=D.stages.dispatch.split('\n').filter(Boolean).slice(0,3).map(l=>`<li>${esc(l.slice(0,90))}${l.length>90?'…':''}</li>`);
  inRows.push('<li>full dispatch plan</li>');
}
let toolRows=CFG.tools.map(n=>`<li><b>${esc(n)}</b>${tc[n]?` <span class="cnt">×${tc[n]}</span>`:''}</li>`);
if(CFG.note)toolRows.push(`<li>${esc(CFG.note)}</li>`);
if(!CFG.tools.length&&!CFG.note)toolRows.push('<li>—</li>');
const outLines=D.stages[key].split('\n').filter(Boolean).slice(0,4).map(l=>esc(l.slice(0,120))+(l.length>120?'…':'')).join('\n');
el.innerHTML=`<div class="con-h"><span class="led" aria-hidden="true"></span><b>${CFG.name}</b><span class="con-st">STATUS: COMPLETED</span><span class="chip">RECORDED RUN</span></div>
<div class="con-g"><div class="con-c"><h5>▸ INPUT</h5><ul>${inRows.join('')}</ul></div>
<div class="con-c"><h5>▸ TOOL CALLS</h5><ul>${toolRows.join('')}</ul></div>
<div class="con-c"><h5>▸ OUTPUT (EXCERPT)</h5><div class="con-out">${outLines}<span class="cursor" style="display:inline-block;width:7px;height:13px;background:var(--sig);vertical-align:-2px"></span></div></div></div>
<div class="con-f">RECORDED REAL RUN · MODEL ${esc(D.meta.model)} · ${D.meta.seconds}S END TO END · FULL REPLAY ON <a href="demo.html">LIVE REPLAY</a></div>`;
el.querySelectorAll('li,.con-out,.con-h').forEach((n,i)=>{n.classList.add('st');n.style.animationDelay=(i*0.14)+'s'});
})();
