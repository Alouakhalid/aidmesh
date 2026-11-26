/* Crisis globe: a command view of where reports land.
   Recorded-run incidents (Alexandria) plot by default; the region picker
   geocodes any place worldwide via OpenStreetMap Nominatim; live-run
   incidents plot via window.__aidmeshPlotLive. */
import * as THREE from 'https://cdn.jsdelivr.net/npm/three@0.160.0/build/three.module.js';
const cv=document.getElementById('globe');
if(cv){
const reduced=matchMedia('(prefers-reduced-motion: reduce)').matches;
const wrap=cv.parentElement;
const renderer=new THREE.WebGLRenderer({canvas:cv,antialias:true,alpha:true});
const scene=new THREE.Scene();
const cam=new THREE.PerspectiveCamera(42,1,0.1,100);cam.position.set(0,0,3.1);
const world=new THREE.Group();scene.add(world);
const sphere=new THREE.Mesh(new THREE.SphereGeometry(1,36,36),new THREE.MeshBasicMaterial({color:0x1c3a28,wireframe:true,transparent:true,opacity:0.5}));
world.add(sphere);
const dots=new THREE.BufferGeometry();const dp=[];
for(let i=0;i<420;i++){const u=Math.random()*2*Math.PI,v=Math.acos(2*Math.random()-1);dp.push(Math.sin(v)*Math.cos(u)*1.002,Math.cos(v)*1.002,Math.sin(v)*Math.sin(u)*1.002)}
dots.setAttribute('position',new THREE.Float32BufferAttribute(dp,3));
world.add(new THREE.Points(dots,new THREE.PointsMaterial({color:0x57ff9a,size:0.008,transparent:true,opacity:0.35})));
const ll=(lat,lon,r=1)=>{const phi=(90-lat)*Math.PI/180,th=(lon+180)*Math.PI/180;return new THREE.Vector3(-r*Math.sin(phi)*Math.cos(th),r*Math.cos(phi),r*Math.sin(phi)*Math.sin(th))};
const pulses=[];
function mark(lat,lon,color,label){
 const g=new THREE.Group();g.position.copy(ll(lat,lon,1.01));g.lookAt(0,0,0);
 const dot=new THREE.Mesh(new THREE.SphereGeometry(0.02,10,10),new THREE.MeshBasicMaterial({color}));g.add(dot);
 const ring=new THREE.Mesh(new THREE.RingGeometry(0.03,0.038,28),new THREE.MeshBasicMaterial({color,side:THREE.DoubleSide,transparent:true,opacity:0.9}));
 g.add(ring);pulses.push({ring,t:Math.random()*Math.PI*2});
 world.add(g);return g}
let targetQ=null;
function flyTo(lat,lon){
 const from=world.quaternion.clone();
 const to=new THREE.Quaternion().setFromUnitVectors(ll(lat,lon).normalize(),new THREE.Vector3(0,0,1));
 targetQ={from,to,t:0}}
/* recorded Alexandria run: positions geocoded via OpenStreetMap, approximate */
const ALX=[
 {id:'R1+R2',need:'rescue',loc:'Manshiya district',lat:31.1965,lon:29.8890,life:true},
 {id:'R3',need:'water / baby formula',loc:'Agami shelter school',lat:31.0986,lon:29.7614,life:false},
 {id:'R4',need:'hazard · live wire',loc:'Corniche near Stanley Bridge',lat:31.2350,lon:29.9486,life:true},
 {id:'R5',need:'dam-collapse rumour',loc:'Alexandria (city-wide claim)',lat:31.2001,lon:29.9187,life:true,rumour:true},
 {id:'R6',need:'medical · dialysis',loc:'Sidi Gaber clinic',lat:31.2190,lon:29.9424,life:true}];
const list=document.getElementById('geolist'),stat=document.getElementById('geostat');
function legend(items,mode){
 list.innerHTML=items.map(i=>`<li><i style="background:${i.rumour?'var(--red)':i.life?'var(--amb)':'var(--sig)'}"></i><b>${i.id}</b> ${i.need} · ${i.loc}${i.life?' · LIFE-THREATENING':''}${i.rumour?' · RUMOUR (killed)':''}</li>`).join('')||'<li>No incidents plotted for this region yet.</li>'}
let alxShown=false;
function showAlexandria(){
 if(alxShown)return;alxShown=true;
 stat.textContent='RECORDED RUN · ALEXANDRIA, EGYPT · POSITIONS APPROXIMATE (OSM) · SAMPLE RESOURCE REGISTRY';
 ALX.forEach((i,n)=>setTimeout(()=>{mark(i.lat,i.lon,i.rumour?0xff5b5b:i.life?0xffb454:0x57ff9a);if(n===0)legend(ALX)},n*450));
 flyTo(31.2,29.92)}
async function geocode(q){
 const r=await fetch('https://nominatim.openstreetmap.org/search?q='+encodeURIComponent(q)+'&format=json&limit=1',{headers:{'Accept':'application/json'}});
 if(!r.ok)throw new Error('geocode HTTP '+r.status);
 const j=await r.json();if(!j.length)throw new Error('place not found');
 return{lat:+j[0].lat,lon:+j[0].lon,name:j[0].display_name.split(',').slice(0,2).join(',')}}
document.getElementById('geogo').onclick=async()=>{
 const q=document.getElementById('geoin').value.trim();if(!q)return;
 stat.textContent='GEOCODING…';
 try{
  const g=await geocode(q);
  flyTo(g.lat,g.lon);
  if(Math.abs(g.lat-31.2)<0.6&&Math.abs(g.lon-29.92)<0.6){showAlexandria()}
  else{stat.textContent='LIVE-ONLY DEMO REGION · '+g.name.toUpperCase()+' · GEOCODING WORKS WORLDWIDE; RECORDED DATA AND THE RESOURCE REGISTRY ARE ALEXANDRIA ONLY · RUN A LIVE REPORT BELOW TO PLOT THIS REGION';
   legend([])}
 }catch(e){stat.textContent='GEOCODE FAILED: '+String(e.message).toUpperCase()+' · TRY ANOTHER SPELLING'}};
/* live-run hook: geocode and plot live incidents, honestly labeled */
window.__aidmeshPlotLive=async incidents=>{
 const plotted=[];
 for(const inc of incidents.slice(0,6)){
  try{const g=await geocode(String(inc.location||''));mark(g.lat,g.lon,inc.life_threatening?0xffb454:0x57ff9a);
   plotted.push({id:inc.report_id||('L'+(plotted.length+1)),need:inc.need||'report',loc:g.name,life:!!inc.life_threatening});
   if(plotted.length===1)flyTo(g.lat,g.lon)}catch(e){}
  await new Promise(r=>setTimeout(r,1100))}
 if(plotted.length){stat.textContent='LIVE RUN · PLOTTED FROM YOUR REPORT · RESOURCE REGISTRY IS SAMPLE DATA (ALEXANDRIA ONLY)';legend(plotted)}};
function size(){const w=wrap.clientWidth,h=Math.max(340,Math.min(520,w*0.55));renderer.setSize(w,h);renderer.setPixelRatio(Math.min(devicePixelRatio,2));cam.aspect=w/h;cam.updateProjectionMatrix()}
size();addEventListener('resize',size);
const clock=new THREE.Clock();
(function loop(){requestAnimationFrame(loop);const t=clock.getElapsedTime();
 if(targetQ){targetQ.t=Math.min(1,targetQ.t+0.02);world.quaternion.slerpQuaternions(targetQ.from,targetQ.to,targetQ.t<.5?2*targetQ.t*targetQ.t:1-Math.pow(-2*targetQ.t+2,2)/2);if(targetQ.t>=1)targetQ=null}
 else if(!reduced)world.rotation.y+=0.0012;
 for(const p of pulses){const s=1+((t*0.9+p.t)%1.6);p.ring.scale.setScalar(reduced?1:s);p.ring.material.opacity=reduced?0.9:Math.max(0,1.1-((t*0.9+p.t)%1.6)/1.6)}
 renderer.render(scene,cam)})();
showAlexandria();
}
