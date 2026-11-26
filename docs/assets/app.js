import * as THREE from 'https://cdn.jsdelivr.net/npm/three@0.160.0/build/three.module.js';

/* ---------- page transitions ---------- */
const wipe=document.createElement('div');wipe.id='wipe';document.body.appendChild(wipe);
wipe.classList.add('out');
document.addEventListener('click',e=>{
  const a=e.target.closest('a[href]');if(!a)return;
  const u=new URL(a.href,location.href);
  if(u.origin!==location.origin||a.target==='_blank'||u.hash&&u.pathname===location.pathname)return;
  if(u.pathname===location.pathname)return;
  e.preventDefault();wipe.classList.remove('out');wipe.classList.add('in');
  setTimeout(()=>location.href=u.href,430);
});
addEventListener('pageshow',e=>{if(e.persisted){wipe.classList.remove('in');wipe.classList.add('out')}});

/* ---------- burger ---------- */
const bg=document.getElementById('burger');
if(bg)bg.onclick=()=>document.getElementById('links').classList.toggle('open');

/* ---------- reveal on scroll ---------- */
const io=new IntersectionObserver(es=>es.forEach(e=>{
  if(!e.isIntersecting)return;e.target.classList.add('in');
  const b=e.target.querySelector('[data-n]');
  if(b){const n=+b.dataset.n;let c=0;const id=setInterval(()=>{b.textContent=++c;if(c>=n)clearInterval(id)},110)}
}),{threshold:.25});
document.querySelectorAll('.card,.feat,.step').forEach(c=>io.observe(c));

/* ---------- 3D backgrounds (one per page) ---------- */
const cv=document.getElementById('bg');
const r=new THREE.WebGLRenderer({canvas:cv,antialias:true,alpha:true});
r.setPixelRatio(Math.min(devicePixelRatio,2));
const sc=new THREE.Scene();const cam=new THREE.PerspectiveCamera(60,1,.1,300);cam.position.z=26;
function rs(){r.setSize(innerWidth,innerHeight);cam.aspect=innerWidth/innerHeight;cam.updateProjectionMatrix()}rs();addEventListener('resize',rs);
let mx=0,my=0;addEventListener('pointermove',e=>{mx=e.clientX/innerWidth-.5;my=e.clientY/innerHeight-.5});
const G=new THREE.Group();sc.add(G);
const scene=document.body.dataset.scene||'mesh';

function stars(n,spread,cols){const pts=[];
  for(let i=0;i<n;i++){const m=new THREE.Mesh(new THREE.SphereGeometry(.12,8,8),new THREE.MeshBasicMaterial({color:cols[i%cols.length]}));
    m.position.set((Math.random()-.5)*spread,(Math.random()-.5)*spread*.6,(Math.random()-.5)*spread*.5);
    m.userData.v=new THREE.Vector3((Math.random()-.5)*.008,(Math.random()-.5)*.008,(Math.random()-.5)*.008);G.add(m);pts.push(m)}return pts}
const drift=(pts,L)=>pts.forEach(p=>{p.position.add(p.userData.v);['x','y','z'].forEach((k,i)=>{if(Math.abs(p.position[k])>L[i])p.userData.v[k]*=-1})});

let tick;
if(scene==='mesh'||scene==='demo'){
  const pts=stars(64,40,[0x22d3ee,0xa78bfa,0xfb7185]);
  const lg=new THREE.BufferGeometry();G.add(new THREE.LineSegments(lg,new THREE.LineBasicMaterial({color:0x6d7cff,transparent:true,opacity:.22})));
  const core=new THREE.Mesh(new THREE.IcosahedronGeometry(3,1),new THREE.MeshBasicMaterial({color:0x22d3ee,wireframe:true,transparent:true,opacity:.3}));G.add(core);
  tick=t=>{drift(pts,[22,14,11]);const a=[];
    for(let i=0;i<pts.length;i++)for(let j=i+1;j<pts.length;j++)if(pts[i].position.distanceTo(pts[j].position)<7)a.push(...pts[i].position.toArray(),...pts[j].position.toArray());
    lg.setAttribute('position',new THREE.Float32BufferAttribute(a,3));
    core.rotation.x=t*.0003;core.rotation.y=t*.0005;core.scale.setScalar(1+Math.sin(t*.002)*.08)};
}
else if(scene==='globe'){
  const globe=new THREE.Mesh(new THREE.SphereGeometry(9,28,20),new THREE.MeshBasicMaterial({color:0x22d3ee,wireframe:true,transparent:true,opacity:.14}));G.add(globe);
  const marks=[];const cols=[0xfb7185,0xfbbf24,0x34d399,0x22d3ee];
  for(let i=0;i<14;i++){const m=new THREE.Mesh(new THREE.SphereGeometry(.22,10,10),new THREE.MeshBasicMaterial({color:cols[i%4]}));
    const th=Math.random()*Math.PI*2,ph=Math.acos(2*Math.random()-1);
    m.position.setFromSphericalCoords(9.1,ph,th);m.userData.ph=Math.random()*Math.PI*2;globe.add(m);marks.push(m)}
  tick=t=>{globe.rotation.y=t*.00015;globe.rotation.x=.25;
    marks.forEach(m=>{const s=1+Math.sin(t*.004+m.userData.ph)*.6;m.scale.setScalar(Math.max(.2,s))})};
}
else if(scene==='verify'){
  const shield=new THREE.Mesh(new THREE.OctahedronGeometry(5,0),new THREE.MeshBasicMaterial({color:0x34d399,wireframe:true,transparent:true,opacity:.35}));G.add(shield);
  const ring1=new THREE.Mesh(new THREE.TorusGeometry(7.5,.05,8,80),new THREE.MeshBasicMaterial({color:0x22d3ee,transparent:true,opacity:.5}));
  const ring2=ring1.clone();ring2.rotation.x=Math.PI/2.4;G.add(ring1,ring2);
  const pts=stars(40,44,[0x34d399,0x22d3ee,0xfb7185]);
  tick=t=>{drift(pts,[24,15,12]);shield.rotation.y=t*.0004;shield.rotation.x=Math.sin(t*.0003)*.3;
    ring1.rotation.z=t*.0006;ring2.rotation.y=t*.0005};
}
else if(scene==='triage'){
  const mk=(y,r,c)=>{const m=new THREE.Mesh(new THREE.ConeGeometry(r,2.6,4,1,true),new THREE.MeshBasicMaterial({color:c,wireframe:true,transparent:true,opacity:.55}));m.position.y=y;m.rotation.y=Math.PI/4;G.add(m);return m};
  const p1=mk(3.4,1.8,0xfb7185),p2=mk(.6,3.2,0xfbbf24),p3=mk(-2.4,4.6,0x22d3ee);
  const pts=stars(46,44,[0xfb7185,0xfbbf24,0x22d3ee]);
  tick=t=>{drift(pts,[24,15,12]);
    p1.rotation.y=t*.0009;p2.rotation.y=-t*.0007;p3.rotation.y=t*.0005;
    p1.position.y=3.4+Math.sin(t*.002)*.25;p2.position.y=.6+Math.sin(t*.002+2)*.2;p3.position.y=-2.4+Math.sin(t*.002+4)*.15};
}
else if(scene==='dispatch'){
  const hub=new THREE.Mesh(new THREE.IcosahedronGeometry(1.6,1),new THREE.MeshBasicMaterial({color:0xfbbf24,wireframe:true}));G.add(hub);
  const targets=[],arcs=[];
  for(let i=0;i<7;i++){const m=new THREE.Mesh(new THREE.SphereGeometry(.4,10,10),new THREE.MeshBasicMaterial({color:i%2?0x22d3ee:0xa78bfa}));
    m.position.set((Math.random()-.5)*30,(Math.random()-.5)*16,(Math.random()-.5)*8);G.add(m);targets.push(m);
    const mid=hub.position.clone().lerp(m.position,.5);mid.z+=6;
    const cur=new THREE.QuadraticBezierCurve3(hub.position.clone(),mid,m.position.clone());
    const l=new THREE.Line(new THREE.BufferGeometry().setFromPoints(cur.getPoints(24)),new THREE.LineBasicMaterial({color:0x22d3ee,transparent:true,opacity:.3}));G.add(l);arcs.push(l);
    const dot=new THREE.Mesh(new THREE.SphereGeometry(.16,8,8),new THREE.MeshBasicMaterial({color:0xffffff}));G.add(dot);m.userData={cur,dot,off:Math.random()}}
  tick=t=>{hub.rotation.y=t*.0006;
    targets.forEach(m=>{const u=m.userData;const p=(t*.00035+u.off)%1;u.dot.position.copy(u.cur.getPoint(p))})};
}
else if(scene==='alert'){
  const rings=[];
  for(let i=0;i<4;i++){const ring=new THREE.Mesh(new THREE.TorusGeometry(1,.07,8,90),new THREE.MeshBasicMaterial({color:i%2?0x22d3ee:0xfb7185,transparent:true,opacity:.6}));G.add(ring);rings.push(ring)}
  const core=new THREE.Mesh(new THREE.SphereGeometry(.8,16,16),new THREE.MeshBasicMaterial({color:0xffffff}));G.add(core);
  const pts=stars(40,44,[0x22d3ee,0xfb7185,0xa78bfa]);
  tick=t=>{drift(pts,[24,15,12]);core.scale.setScalar(1+Math.sin(t*.006)*.15);
    rings.forEach((ring,i)=>{const p=(t*.0004+i/rings.length)%1;ring.scale.setScalar(1+p*11);ring.material.opacity=.6*(1-p);ring.rotation.x=t*.0003+i})};
}
function loop(t){requestAnimationFrame(loop);
  G.rotation.y+=(mx*.9-G.rotation.y)*.04;G.rotation.x+=(my*.5-G.rotation.x)*.04;
  if(tick)tick(t);r.render(sc,cam)}
requestAnimationFrame(loop);
