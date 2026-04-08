/* ===================================================================
   SUPERCINE PRO ASSURDA — Engine
   Platformer cinematografico. 7 zone, stelle, ostacoli, powerup, rank.
   =================================================================== */

// ========== CONFIG ==========
export const TW = 24, GROUND_Y = 350, LEVEL_H = 420, CAM_SMOOTH = 0.08;
export const GRAV = 820, JUMP_V = -370, RUN_SPD = 175, MAX_FALL = 520;
export const COYOTE = 0.1, JBUF = 0.12, INV_DUR = 1.5, MAX_HP = 3;
export const CONTEST_T = 120, SOLO_T = 180;
export const PW = 18, PH = 26;
export const ZONE_NAMES = ['BACKLOT ARCADE','SET FANTASY','ZONA STUNT PRO','CAMERA CRANE','SET SEGRETO','STUDIO COLLAPSATO','PREMIERE FINISH'];
export const ZONE_COLORS = [
  {bg1:'#1a0a30',bg2:'#2a1540',plat:'#f5a623',platL:'#ffd700',acc:'#ff6600'},
  {bg1:'#0a0a30',bg2:'#1a1050',plat:'#9b59b6',platL:'#c39bd3',acc:'#8e44ad'},
  {bg1:'#2a0a0a',bg2:'#3a1515',plat:'#e74c3c',platL:'#ff6b6b',acc:'#ff4444'},
  {bg1:'#0a1a2a',bg2:'#102535',plat:'#1abc9c',platL:'#2ecc71',acc:'#00d4aa'},
  {bg1:'#2a1a00',bg2:'#3a2a10',plat:'#f1c40f',platL:'#ffd700',acc:'#ff3366'},
  {bg1:'#1a0015',bg2:'#2a0020',plat:'#8e44ad',platL:'#c39bd3',acc:'#ff0066'},
  {bg1:'#0a0a20',bg2:'#1a1a40',plat:'#f39c12',platL:'#ffd700',acc:'#00ffaa'},
];

// ========== HELPERS ==========
export const lerp = (a,b,t) => a+(b-a)*Math.min(1,t);
export const clamp = (v,lo,hi) => Math.max(lo,Math.min(hi,v));
export const rand = (a,b) => Math.random()*(b-a)+a;
export const aabb = (a,b) => a.x<b.x+b.w && a.x+a.w>b.x && a.y<b.y+b.h && a.y+a.h>b.y;

// ========== LEVEL GENERATION ==========
export function generateLevel() {
  const P=[],S=[],O=[],CK=[],SEC=[],PW_=[],FIN={x:4650,y:GROUND_Y-40};
  const g=(x,w)=>P.push({x,y:GROUND_Y,w,h:50,type:'ground',zone:0});
  const p=(x,y,w,t='plat',z=0)=>P.push({x,y,w,h:16,type:t,zone:z});
  const b=(x,y,z=0)=>P.push({x,y,w:TW,h:TW,type:'ciak',zone:z,hit:false,hasStar:Math.random()>0.5});
  const st=(x,y,t='normal')=>S.push({x,y,type:t,collected:false});
  const ob=(x,y,w,h,t,props={})=>O.push({x,y,w,h,type:t,active:true,...props,ox:x,oy:y});
  const ck=(x)=>CK.push({x,y:GROUND_Y-30,activated:false});
  const sec=(x,y,w,h)=>SEC.push({x,y,w,h,found:false});
  const pw=(x,y,t)=>PW_.push({x,y,type:t,collected:false});

  // === ZONE 1: BACKLOT ARCADE (0-800) ===
  g(0,820);
  p(100,280,70,'plat',0); p(220,240,60,'plat',0); p(350,260,80,'plat',0); p(500,220,60,'plat',0); p(620,280,70,'plat',0);
  b(130,256,0); b(250,216,0); b(530,196,0);
  for(let i=0;i<8;i++) st(60+i*90,GROUND_Y-20);
  st(130,260); st(250,220); st(380,240); st(530,200); st(650,260);
  ob(400,GROUND_Y-24,24,24,'ciak_rebel',{vx:40,range:60,phase:0});
  ob(700,GROUND_Y-24,24,24,'ciak_rebel',{vx:-35,range:50,phase:0});

  // === ZONE 2: SET FANTASY (800-1600) ===
  g(820,400); g(1280,340);
  p(870,280,80,'plat',1); p(980,230,60,'plat',1); p(1100,200,70,'tramp',1);
  p(1200,260,50,'plat',1); p(1320,220,80,'plat',1); p(1450,180,60,'plat',1);
  b(910,256,1); b(1010,206,1); b(1350,196,1);
  for(let i=0;i<6;i++) st(850+i*70,GROUND_Y-20);
  st(900,260); st(1010,210); st(1130,180); st(1230,240); st(1350,200); st(1480,160);
  st(1140,160,'mega');
  ob(950,200,20,40,'boom_mic',{vy:0,range:60,phase:0,swing:true});
  ob(1400,220,20,20,'drone',{vx:50,range:100,phase:0});
  pw(1100,170,'sprint');
  sec(1550,260,60,90);
  st(1560,280); st(1580,300);

  // === ZONE 3: STUNT PRO (1600-2400) ===
  g(1620,200); g(1900,150); g(2120,200);
  p(1650,280,60,'plat',2); p(1750,230,50,'moving',2); p(1870,200,60,'plat',2);
  p(1950,260,70,'plat',2); p(2050,180,50,'moving',2); p(2180,220,60,'plat',2); p(2300,260,80,'plat',2);
  b(1680,256,2); b(1980,236,2); b(2210,196,2);
  for(let i=0;i<5;i++) st(1650+i*80,GROUND_Y-20);
  st(1680,260); st(1780,210); st(1900,180); st(1980,240); st(2080,160); st(2210,200); st(2330,240);
  ob(1800,180,20,40,'boom_mic',{vy:0,range:80,phase:1,swing:true});
  ob(2000,GROUND_Y-24,30,20,'cart',{vx:60,range:120,phase:0});
  ob(2250,140,24,24,'drone',{vx:-40,range:80,phase:0.5});
  ck(1950);
  pw(2050,150,'megaciak');

  // === ZONE 4: CAMERA CRANE (2400-3200) ===
  g(2400,300); g(2780,240); g(3080,200);
  // High path (risky, more stars)
  p(2450,250,50,'plat',3); p(2530,200,50,'plat',3); p(2620,150,60,'moving',3); p(2720,120,50,'plat',3);
  p(2820,100,60,'plat',3); p(2930,130,50,'moving',3); p(3020,160,60,'plat',3);
  // Low path (safer)
  p(2450,310,80,'plat',3); p(2580,310,60,'plat',3); p(2700,320,80,'plat',3); p(2850,310,60,'plat',3); p(2980,320,80,'plat',3);
  b(2560,176,3); b(2650,126,3); b(2850,76,3);
  // High path stars
  st(2480,230); st(2560,180); st(2650,130); st(2750,100); st(2850,80); st(2960,110); st(3050,140);
  st(2650,100,'mega');
  // Low path stars
  for(let i=0;i<4;i++) st(2480+i*130,GROUND_Y-20);
  ob(2600,100,24,24,'drone',{vx:50,range:120,phase:0});
  ob(2900,80,20,40,'boom_mic',{vy:0,range:100,phase:0.3,swing:true});
  // Secret entrance (high up in zone 4)
  p(2800,50,40,'secret_entry',3);
  sec(2800,20,50,40);
  st(2810,0,'mega'); st(2830,0,'mega');
  ck(2700);
  pw(2820,70,'stella');

  // === ZONE 5: SECRET PREMIERE (hidden vertical area above zone 4) ===
  p(2780,-30,80,'plat',4); p(2850,-80,60,'plat',4); p(2920,-130,70,'plat',4); p(2800,-180,100,'plat',4);
  for(let i=0;i<6;i++) st(2790+i*25,-50-i*25,'mega');
  pw(2840,-200,'stella');

  // === ZONE 6: STUDIO COLLAPSATO (3200-4200) ===
  g(3200,300); g(3580,200); g(3850,250);
  p(3250,280,50,'plat',5); p(3330,240,60,'moving',5); p(3420,200,50,'plat',5);
  p(3520,260,60,'plat',5); p(3620,200,70,'moving',5); p(3730,240,50,'plat',5);
  p(3830,200,60,'plat',5); p(3940,260,80,'plat',5); p(4060,220,60,'moving',5); p(4150,280,70,'plat',5);
  b(3280,256,5); b(3450,176,5); b(3860,176,5);
  for(let i=0;i<8;i++) st(3230+i*110,GROUND_Y-20);
  st(3280,260); st(3360,220); st(3450,180); st(3550,240); st(3650,180); st(3760,220); st(3860,180); st(3970,240); st(4090,200); st(4180,260);
  ob(3300,GROUND_Y-24,30,20,'cart',{vx:80,range:100,phase:0});
  ob(3500,180,24,24,'drone',{vx:-60,range:100,phase:0});
  ob(3700,160,20,40,'boom_mic',{vy:0,range:70,phase:0.7,swing:true});
  ob(3900,GROUND_Y-24,30,20,'cart',{vx:-70,range:120,phase:0.5});
  ob(4100,200,24,24,'ciak_rebel',{vx:50,range:80,phase:0});
  ck(3600);
  sec(4050,140,50,80);
  st(4060,160); st(4080,160);

  // === ZONE 7: PREMIERE FINISH (4200-4800) ===
  g(4200,600);
  p(4300,300,60,'plat',6); p(4400,260,60,'plat',6); p(4500,300,80,'plat',6);
  for(let i=0;i<10;i++) st(4220+i*50,GROUND_Y-20);
  st(4330,280); st(4430,240); st(4530,280);
  // Celebration area
  p(4600,280,100,'finish',6);

  // Set zones on ground platforms
  P.forEach(pl => { if(pl.zone===0) { const z=pl.x<800?0:pl.x<1600?1:pl.x<2400?2:pl.x<3200?3:pl.x<4200?5:6; pl.zone=z; }});

  return {platforms:P,stars:S,obstacles:O,checkpoints:CK,secrets:SEC,powerups:PW_,finish:FIN,
    totalStars:S.length,totalSecrets:SEC.length,levelWidth:4800};
}

// ========== ZONE FOR X ==========
export function zoneForX(x){return x<800?0:x<1600?1:x<2400?2:x<3200?3:x<4200?5:6;}

// ========== INIT GAME ==========
export function initGame(w,h,mode){
  const level = generateLevel();
  return {
    w,h,mode,level,
    player:{x:40,y:GROUND_Y-PH-2,vx:0,vy:0,grounded:false,facing:1,running:false,
      coyoteT:0,jbufT:0,hp:MAX_HP,invuln:0,frame:0,animT:0},
    cam:{x:0,y:0},
    input:{left:false,right:false,jump:false,jumpPressed:false},
    time:mode==='contest'?CONTEST_T:SOLO_T,
    stars:0,damage:0,secretsFound:0,completed:false,
    lastCkX:40,lastCkY:GROUND_Y-PH-2,
    activePowerup:null,powerupT:0,
    particles:[],phase:'intro',runTime:0,
    zone:0,zoneFlash:0,zoneFlashName:'',
    shakeT:0,
  };
}

// ========== PHYSICS UPDATE ==========
export function updateGame(g,dt){
  if(g.phase!=='play') return;
  dt=Math.min(dt,0.033);
  const p=g.player, inp=g.input, lv=g.level;
  g.runTime+=dt;
  g.time-=dt; if(g.time<=0){g.time=0;g.phase='over';return;}
  if(g.shakeT>0) g.shakeT-=dt;
  if(g.powerupT>0){g.powerupT-=dt;if(g.powerupT<=0)g.activePowerup=null;}

  // Input
  const spd = g.activePowerup==='sprint'?RUN_SPD*1.5:RUN_SPD;
  if(inp.left){p.vx=-spd;p.facing=-1;p.running=true;}
  else if(inp.right){p.vx=spd;p.facing=1;p.running=true;}
  else{p.vx=0;p.running=false;}

  // Jump buffer
  if(inp.jumpPressed){p.jbufT=JBUF;inp.jumpPressed=false;}
  if(p.jbufT>0)p.jbufT-=dt;

  // Coyote time
  if(p.grounded)p.coyoteT=COYOTE; else p.coyoteT-=dt;

  // Jump
  if(p.jbufT>0&&p.coyoteT>0){
    p.vy=JUMP_V;p.grounded=false;p.coyoteT=0;p.jbufT=0;
    spawnParticles(g,p.x+PW/2,p.y+PH,4,'#fff',40);
  }
  // Variable jump
  if(!inp.jump&&p.vy<-100)p.vy*=0.85;

  // Gravity
  p.vy+=GRAV*dt; p.vy=Math.min(p.vy,MAX_FALL);

  // Move X
  p.x+=p.vx*dt;
  p.x=clamp(p.x,0,lv.levelWidth-PW);

  // Collide X with platforms
  const pb={x:p.x,y:p.y,w:PW,h:PH};
  for(const pl of lv.platforms){
    if(!aabb(pb,pl))continue;
    if(p.vx>0){p.x=pl.x-PW;pb.x=p.x;}
    else if(p.vx<0){p.x=pl.x+pl.w;pb.x=p.x;}
  }

  // Move Y
  const oldY=p.y;
  p.y+=p.vy*dt;
  pb.y=p.y;
  p.grounded=false;

  for(const pl of lv.platforms){
    if(!aabb(pb,pl))continue;
    if(p.vy>0&&oldY+PH<=pl.y+4){
      // Land on top
      p.y=pl.y-PH;p.vy=0;p.grounded=true;
      if(pl.type==='tramp'){p.vy=JUMP_V*1.4;p.grounded=false;spawnParticles(g,p.x+PW/2,p.y+PH,6,ZONE_COLORS[pl.zone||0].acc,60);}
    }else if(p.vy<0&&oldY>=pl.y+pl.h-4){
      // Hit head
      p.y=pl.y+pl.h;p.vy=0;
      if(pl.type==='ciak'&&!pl.hit){
        pl.hit=true;
        spawnParticles(g,pl.x+pl.w/2,pl.y,8,'#ffd700',50);
        if(pl.hasStar){const sx=pl.x+pl.w/2,sy=pl.y-12;lv.stars.push({x:sx,y:sy,type:'normal',collected:false});g.particles.push({x:sx,y:sy,vx:0,vy:-30,r:0,c:'#ffd700',life:0.6,ml:0.6,txt:'STAR!'});}
      }
    }else{
      // Side collision
      if(p.vx>0){p.x=pl.x-PW;}else{p.x=pl.x+pl.w;}
    }
    pb.x=p.x;pb.y=p.y;
  }

  // Fall off
  if(p.y>LEVEL_H+50){
    g.damage++;g.shakeT=0.2;
    p.x=g.lastCkX;p.y=g.lastCkY;p.vx=0;p.vy=0;p.hp=MAX_HP;
    spawnParticles(g,p.x+PW/2,p.y+PH/2,10,'#ff4444',60);
  }

  // Invuln
  if(p.invuln>0)p.invuln-=dt;
  p.animT+=dt;

  // Moving platforms/obstacles update
  for(const o of lv.obstacles){
    if(!o.active)continue;
    if(o.swing){
      o.y=o.oy+Math.sin((g.runTime+o.phase)*2)*o.range;
    }else{
      o.x=o.ox+Math.sin((g.runTime+o.phase)*2)*(o.range||0);
      if(o.vx&&!o.range){o.x+=o.vx*dt;if(o.x<o.ox-100||o.x>o.ox+100)o.vx*=-1;}
    }
  }
  // Moving platforms
  for(const pl of lv.platforms){
    if(pl.type==='moving'){pl.x=pl.x+(pl._ox===undefined?(pl._ox=pl.x,0):0);pl.x=pl._ox+Math.sin((g.runTime)*1.5)*50;}
  }

  // Stars
  for(const s of lv.stars){
    if(s.collected)continue;
    const sr={x:s.x-8,y:s.y-8,w:16,h:16};
    if(aabb(pb,sr)||(g.activePowerup==='stella'&&Math.hypot(s.x-p.x-PW/2,s.y-p.y-PH/2)<50)){
      s.collected=true;g.stars++;
      const pts=s.type==='mega'?20:5;
      spawnParticles(g,s.x,s.y,6,'#ffd700',40);
      g.particles.push({x:s.x,y:s.y-10,vx:0,vy:-25,r:0,c:'#ffd700',life:0.7,ml:0.7,txt:s.type==='mega'?'MEGA!':'+'+pts});
    }
  }

  // Powerups
  for(const pw of lv.powerups){
    if(pw.collected)continue;
    const pr={x:pw.x-10,y:pw.y-10,w:20,h:20};
    if(aabb(pb,pr)){
      pw.collected=true;g.activePowerup=pw.type;g.powerupT=pw.type==='stella'?6:8;
      spawnParticles(g,pw.x,pw.y,10,pw.type==='sprint'?'#00ffff':pw.type==='megaciak'?'#ff6600':'#ffd700',50);
      g.particles.push({x:pw.x,y:pw.y-15,vx:0,vy:-20,r:0,c:'#fff',life:1,ml:1,txt:pw.type==='sprint'?'SPRINT!':pw.type==='megaciak'?'MEGACIAK!':'STELLA!'});
    }
  }

  // Checkpoints
  for(const ck of lv.checkpoints){
    if(ck.activated)continue;
    if(Math.abs(p.x-ck.x)<30&&Math.abs(p.y+PH-ck.y-30)<40){
      ck.activated=true;g.lastCkX=ck.x;g.lastCkY=ck.y-PH;
      spawnParticles(g,ck.x,ck.y,12,'#00ff66',60);
      g.particles.push({x:ck.x,y:ck.y-20,vx:0,vy:-25,r:0,c:'#00ff66',life:1.2,ml:1.2,txt:'AZIONE!'});
    }
  }

  // Secrets
  for(const sc of lv.secrets){
    if(sc.found)continue;
    const sr={x:sc.x,y:sc.y,w:sc.w,h:sc.h};
    if(aabb(pb,sr)){sc.found=true;g.secretsFound++;g.particles.push({x:sc.x+sc.w/2,y:sc.y,vx:0,vy:-30,r:0,c:'#ff00ff',life:1.5,ml:1.5,txt:'SEGRETO!'});}
  }

  // Obstacles collision
  if(p.invuln<=0){
    for(const o of lv.obstacles){
      if(!o.active)continue;
      const or={x:o.x-o.w/2,y:o.y-o.h/2,w:o.w,h:o.h};
      if(aabb(pb,or)){
        p.hp--;p.invuln=INV_DUR;g.damage++;g.shakeT=0.3;
        p.vy=-150;
        spawnParticles(g,p.x+PW/2,p.y+PH/2,8,'#ff4444',50);
        if(p.hp<=0){p.hp=MAX_HP;p.x=g.lastCkX;p.y=g.lastCkY;p.vx=0;p.vy=0;}
        break;
      }
    }
  }

  // Finish
  if(!g.completed&&Math.abs(p.x-lv.finish.x)<40&&Math.abs(p.y+PH-lv.finish.y)<40){
    g.completed=true;g.phase='results';
    spawnParticles(g,lv.finish.x,lv.finish.y-20,20,'#ffd700',80);
    spawnParticles(g,lv.finish.x,lv.finish.y-20,15,'#ff00ff',60);
  }

  // Zone detection
  const nz=zoneForX(p.x);
  if(nz!==g.zone){g.zone=nz;g.zoneFlash=2;g.zoneFlashName=ZONE_NAMES[nz]||'';}
  if(g.zoneFlash>0)g.zoneFlash-=dt;

  // Particles
  for(const pt of g.particles){pt.x+=(pt.vx||0)*dt;pt.y+=(pt.vy||0)*dt;pt.life-=dt;}
  g.particles=g.particles.filter(pt=>pt.life>0);

  // Camera
  const tx=p.x+p.facing*40-g.w/2, ty=p.y-g.h*0.4;
  g.cam.x=lerp(g.cam.x,clamp(tx,0,lv.levelWidth-g.w),CAM_SMOOTH*60*dt);
  g.cam.y=lerp(g.cam.y,clamp(ty,-200,GROUND_Y-g.h+100),CAM_SMOOTH*60*dt);
}

function spawnParticles(g,x,y,n,c,spd){
  for(let i=0;i<n;i++){
    const a=rand(0,Math.PI*2);
    g.particles.push({x,y,vx:Math.cos(a)*rand(10,spd),vy:Math.sin(a)*rand(10,spd)-20,r:rand(1,3),c,life:rand(0.3,0.6),ml:0.6});
  }
}

// ========== RENDERING ==========
export function render(ctx,g){
  const {w,h,cam,level:lv,player:p}=g;
  const cx=cam.x,cy=cam.y;

  // Shake
  let sx=0,sy=0;
  if(g.shakeT>0){sx=rand(-3,3);sy=rand(-3,3);}
  ctx.save();ctx.translate(sx,sy);

  // Background
  drawBg(ctx,w,h,cx,g.zone,g.runTime);

  ctx.save();ctx.translate(-cx,-cy);

  // Platforms
  for(const pl of lv.platforms){
    if(pl.x+pl.w<cx-20||pl.x>cx+w+20)continue;
    if(pl.y+pl.h<cy-20||pl.y>cy+h+20)continue;
    drawPlatform(ctx,pl,g);
  }

  // Stars
  for(const s of lv.stars){
    if(s.collected)continue;
    if(s.x<cx-20||s.x>cx+w+20)continue;
    drawStar(ctx,s,g.runTime);
  }

  // Powerups
  for(const pw of lv.powerups){
    if(pw.collected)continue;
    if(pw.x<cx-30||pw.x>cx+w+30)continue;
    drawPowerup(ctx,pw,g.runTime);
  }

  // Checkpoints
  for(const ck of lv.checkpoints){
    if(ck.x<cx-30||ck.x>cx+w+30)continue;
    drawCheckpoint(ctx,ck,g.runTime);
  }

  // Obstacles
  for(const o of lv.obstacles){
    if(!o.active)continue;
    if(o.x<cx-60||o.x>cx+w+60)continue;
    drawObstacle(ctx,o,g.runTime,g.zone);
  }

  // Finish
  if(lv.finish.x>cx-60&&lv.finish.x<cx+w+60) drawFinish(ctx,lv.finish,g.runTime);

  // Player drawn as PNG overlay — skip canvas player
  // drawPlayer(ctx,p,g);

  // Particles
  for(const pt of g.particles){
    if(pt.txt){
      ctx.globalAlpha=pt.life/pt.ml;ctx.font='bold 10px monospace';ctx.fillStyle=pt.c;ctx.textAlign='center';ctx.fillText(pt.txt,pt.x,pt.y);
    }else{
      ctx.globalAlpha=pt.life/pt.ml;ctx.fillStyle=pt.c;ctx.beginPath();ctx.arc(pt.x,pt.y,pt.r,0,Math.PI*2);ctx.fill();
    }
  }
  ctx.globalAlpha=1;

  ctx.restore();// end cam

  // Zone flash
  if(g.zoneFlash>0){
    ctx.globalAlpha=Math.min(1,g.zoneFlash)*0.9;
    ctx.fillStyle='rgba(0,0,0,0.5)';ctx.fillRect(0,h/2-20,w,40);
    ctx.font='bold 14px monospace';ctx.fillStyle='#ffd700';ctx.textAlign='center';ctx.fillText(g.zoneFlashName,w/2,h/2+5);
    ctx.globalAlpha=1;
  }

  ctx.restore();// end shake
}

// --- Background ---
function drawBg(ctx,w,h,camX,zone,t){
  const zc=ZONE_COLORS[zone]||ZONE_COLORS[0];
  const gr=ctx.createLinearGradient(0,0,0,h);
  gr.addColorStop(0,zc.bg1);gr.addColorStop(1,zc.bg2);
  ctx.fillStyle=gr;ctx.fillRect(0,0,w,h);
  // Parallax buildings
  ctx.fillStyle='rgba(255,255,255,0.02)';
  for(let i=0;i<12;i++){
    const bx=((i*70-camX*0.1)%w+w)%w;
    const bh=30+Math.sin(i*1.3)*20;
    ctx.fillRect(bx,h-bh-50,20+i%3*10,bh);
  }
  // Stars in sky
  ctx.fillStyle='rgba(255,255,255,0.15)';
  for(let i=0;i<20;i++){
    const sx=((i*47+13-camX*0.05)%w+w)%w;
    const sy=10+((i*31)%80);
    ctx.fillRect(sx,sy,1+Math.sin(t*2+i)*0.5,1+Math.sin(t*2+i)*0.5);
  }
}

// --- Platform ---
function drawPlatform(ctx,pl,g){
  const zc=ZONE_COLORS[pl.zone||g.zone]||ZONE_COLORS[0];
  if(pl.type==='ground'){
    ctx.fillStyle=zc.plat;ctx.fillRect(pl.x,pl.y,pl.w,pl.h);
    ctx.fillStyle=zc.platL;ctx.fillRect(pl.x,pl.y,pl.w,3);
  }else if(pl.type==='ciak'){
    ctx.fillStyle=pl.hit?'#555':'#222';ctx.fillRect(pl.x,pl.y,pl.w,pl.h);
    if(!pl.hit){ctx.fillStyle='#fff';for(let i=0;i<3;i++)ctx.fillRect(pl.x+2+i*8,pl.y,4,4);ctx.strokeStyle=zc.acc;ctx.lineWidth=1;ctx.strokeRect(pl.x,pl.y,pl.w,pl.h);}
  }else if(pl.type==='tramp'){
    ctx.fillStyle='#333';ctx.fillRect(pl.x,pl.y+6,pl.w,10);
    ctx.fillStyle=zc.acc;ctx.fillRect(pl.x+2,pl.y,pl.w-4,8);
    ctx.shadowBlur=6;ctx.shadowColor=zc.acc;ctx.fillRect(pl.x+2,pl.y,pl.w-4,4);ctx.shadowBlur=0;
  }else if(pl.type==='finish'){
    ctx.fillStyle='#ffd700';ctx.fillRect(pl.x,pl.y,pl.w,pl.h);
    ctx.shadowBlur=10;ctx.shadowColor='#ffd700';ctx.fillRect(pl.x,pl.y,pl.w,4);ctx.shadowBlur=0;
    ctx.font='bold 8px monospace';ctx.fillStyle='#000';ctx.textAlign='center';ctx.fillText('PREMIERE',pl.x+pl.w/2,pl.y+12);
  }else{
    ctx.fillStyle=zc.plat;ctx.fillRect(pl.x,pl.y,pl.w,pl.h);
    ctx.fillStyle=zc.platL;ctx.fillRect(pl.x,pl.y,pl.w,2);
  }
}

// --- Star ---
function drawStar(ctx,s,t){
  ctx.save();ctx.translate(s.x,s.y);
  const sc=1+Math.sin(t*4+s.x)*0.15;ctx.scale(sc,sc);
  const mega=s.type==='mega';
  ctx.shadowBlur=mega?12:6;ctx.shadowColor=mega?'#ff6600':'#ffd700';
  ctx.fillStyle=mega?'#ff6600':'#ffd700';
  ctx.beginPath();
  const r=mega?8:5,inner=mega?3.5:2;
  for(let i=0;i<10;i++){const a=(i*Math.PI/5)-Math.PI/2,rv=i%2===0?r:inner;i===0?ctx.moveTo(Math.cos(a)*rv,Math.sin(a)*rv):ctx.lineTo(Math.cos(a)*rv,Math.sin(a)*rv);}
  ctx.closePath();ctx.fill();ctx.shadowBlur=0;ctx.restore();
}

// --- Powerup ---
function drawPowerup(ctx,pw,t){
  ctx.save();ctx.translate(pw.x,pw.y);
  const bob=Math.sin(t*3)*4;ctx.translate(0,bob);
  const c=pw.type==='sprint'?'#00ffff':pw.type==='megaciak'?'#ff6600':'#ffd700';
  ctx.shadowBlur=10;ctx.shadowColor=c;ctx.fillStyle=c;
  ctx.beginPath();ctx.arc(0,0,9,0,Math.PI*2);ctx.fill();
  ctx.fillStyle='#fff';ctx.font='bold 8px monospace';ctx.textAlign='center';ctx.fillText(pw.type==='sprint'?'S':pw.type==='megaciak'?'M':'P',0,3);
  ctx.shadowBlur=0;ctx.restore();
}

// --- Checkpoint ---
function drawCheckpoint(ctx,ck,t){
  ctx.save();ctx.translate(ck.x,ck.y);
  ctx.fillStyle=ck.activated?'#00ff66':'#444';
  ctx.fillRect(-3,0,6,30);
  if(ck.activated){ctx.shadowBlur=8;ctx.shadowColor='#00ff66';ctx.fillStyle='#00ff66';ctx.fillRect(-8,-5,16,8);ctx.shadowBlur=0;
    ctx.fillStyle='#000';ctx.font='bold 5px monospace';ctx.textAlign='center';ctx.fillText('OK',0,1);
  }else{ctx.fillStyle='#666';ctx.fillRect(-6,-3,12,6);}
  ctx.restore();
}

// --- Obstacle ---
function drawObstacle(ctx,o,t,zone){
  const zc=ZONE_COLORS[zone]||ZONE_COLORS[0];
  ctx.save();ctx.translate(o.x,o.y);
  ctx.shadowBlur=4;ctx.shadowColor='#ff4444';
  switch(o.type){
    case 'ciak_rebel':
      ctx.fillStyle='#222';ctx.fillRect(-12,-8,24,16);ctx.fillStyle='#ff3333';for(let i=0;i<3;i++)ctx.fillRect(-10+i*8,-8,4,4);
      ctx.strokeStyle='#ff4444';ctx.lineWidth=1;ctx.strokeRect(-12,-8,24,16);break;
    case 'drone':
      ctx.fillStyle='#333';ctx.beginPath();ctx.arc(0,0,10,0,Math.PI*2);ctx.fill();
      ctx.fillStyle='#ff0000';ctx.fillRect(-2,-2,4,4);
      ctx.strokeStyle='#666';ctx.lineWidth=1;ctx.beginPath();ctx.moveTo(-14,-4);ctx.lineTo(-8,0);ctx.moveTo(14,-4);ctx.lineTo(8,0);ctx.stroke();break;
    case 'boom_mic':
      ctx.fillStyle='#555';ctx.fillRect(-2,-(o.h/2),4,o.h);
      ctx.fillStyle='#888';ctx.beginPath();ctx.arc(0,-(o.h/2),6,0,Math.PI*2);ctx.fill();
      ctx.fillStyle='#aaa';ctx.fillRect(-8,-(o.h/2)-2,16,4);break;
    case 'cart':
      ctx.fillStyle='#444';ctx.fillRect(-15,-10,30,14);ctx.fillStyle='#ff6600';ctx.fillRect(-12,-8,8,4);
      ctx.fillStyle='#222';ctx.beginPath();ctx.arc(-10,6,4,0,Math.PI*2);ctx.arc(10,6,4,0,Math.PI*2);ctx.fill();break;
  }
  ctx.shadowBlur=0;ctx.restore();
}

// --- Finish ---
function drawFinish(ctx,fin,t){
  ctx.save();ctx.translate(fin.x,fin.y);
  // Red carpet
  ctx.fillStyle='#cc0033';ctx.fillRect(-40,0,80,6);
  // Pillars
  ctx.fillStyle='#ffd700';ctx.fillRect(-45,-60,8,60);ctx.fillRect(37,-60,8,60);
  // Banner
  ctx.shadowBlur=10;ctx.shadowColor='#ffd700';
  ctx.fillStyle='#1a0030';ctx.fillRect(-35,-55,70,22);
  ctx.font='bold 8px monospace';ctx.fillStyle='#ffd700';ctx.textAlign='center';ctx.fillText('PREMIERE',0,-40);
  // Spotlights
  const sw=Math.sin(t*3)*10;
  ctx.globalAlpha=0.1;ctx.fillStyle='#ffd700';
  ctx.beginPath();ctx.moveTo(-45,-60);ctx.lineTo(-60+sw,-120);ctx.lineTo(-30+sw,-120);ctx.closePath();ctx.fill();
  ctx.beginPath();ctx.moveTo(45,-60);ctx.lineTo(30-sw,-120);ctx.lineTo(60-sw,-120);ctx.closePath();ctx.fill();
  ctx.globalAlpha=1;ctx.shadowBlur=0;ctx.restore();
}

// --- Player (Cartoon Director) ---
function drawPlayer(ctx,p,g){
  ctx.save();
  ctx.translate(p.x+PW/2,p.y+PH/2);
  if(p.invuln>0&&Math.sin(p.invuln*20)>0){ctx.globalAlpha=0.4;}
  ctx.scale(p.facing,1);
  const run=p.running&&p.grounded;
  const legAng=run?Math.sin(p.animT*14)*0.5:0;

  // Legs
  ctx.strokeStyle='#2c3e50';ctx.lineWidth=3;ctx.lineCap='round';
  ctx.beginPath();ctx.moveTo(-3,8);ctx.lineTo(-3+Math.sin(legAng)*6,PH/2);ctx.stroke();
  ctx.beginPath();ctx.moveTo(3,8);ctx.lineTo(3-Math.sin(legAng)*6,PH/2);ctx.stroke();
  // Shoes
  ctx.fillStyle='#c0392b';
  ctx.fillRect(-6+Math.sin(legAng)*6,PH/2-3,6,3);
  ctx.fillRect(0-Math.sin(legAng)*6,PH/2-3,6,3);

  // Body
  ctx.fillStyle='#3498db';ctx.fillRect(-6,-2,12,12);
  // Vest
  ctx.fillStyle='#2c3e50';ctx.fillRect(-6,-2,3,12);ctx.fillRect(3,-2,3,12);
  // Belt
  ctx.fillStyle='#f1c40f';ctx.fillRect(-6,7,12,2);

  // Arms
  const armAng=run?Math.sin(p.animT*14)*0.4:Math.sin(p.animT*2)*0.1;
  ctx.strokeStyle='#e8b88a';ctx.lineWidth=2.5;
  ctx.beginPath();ctx.moveTo(-6,2);ctx.lineTo(-10+Math.sin(armAng)*4,8);ctx.stroke();
  ctx.beginPath();ctx.moveTo(6,2);ctx.lineTo(10-Math.sin(armAng)*4,8);ctx.stroke();

  // Head
  ctx.fillStyle='#f5c69a';ctx.beginPath();ctx.arc(0,-7,7,0,Math.PI*2);ctx.fill();
  // Eyes
  ctx.fillStyle='#fff';ctx.beginPath();ctx.arc(-3,-8,2.5,0,Math.PI*2);ctx.fill();ctx.beginPath();ctx.arc(3,-8,2.5,0,Math.PI*2);ctx.fill();
  ctx.fillStyle='#222';ctx.beginPath();ctx.arc(-2.5,-8,1.2,0,Math.PI*2);ctx.fill();ctx.beginPath();ctx.arc(3.5,-8,1.2,0,Math.PI*2);ctx.fill();
  // Mouth
  if(g.activePowerup){ctx.strokeStyle='#e74c3c';ctx.lineWidth=1;ctx.beginPath();ctx.arc(0,-4,2,0,Math.PI);ctx.stroke();}
  else{ctx.fillStyle='#c0392b';ctx.fillRect(-1.5,-5,3,1.5);}
  // Director cap
  ctx.fillStyle='#2c3e50';ctx.fillRect(-7,-14,14,5);
  ctx.fillStyle='#34495e';ctx.beginPath();ctx.ellipse(0,-14,8,3,0,0,Math.PI*2);ctx.fill();
  // Visor
  ctx.fillStyle='#1a1a2e';ctx.fillRect(3,-12,6,3);

  // Megaphone (idle)
  if(!run){
    ctx.fillStyle='#e67e22';ctx.beginPath();ctx.moveTo(8,0);ctx.lineTo(14,-4);ctx.lineTo(14,4);ctx.closePath();ctx.fill();
  }

  // Powerup glow
  if(g.activePowerup){
    ctx.globalAlpha=0.2;ctx.shadowBlur=15;
    ctx.shadowColor=g.activePowerup==='sprint'?'#00ffff':g.activePowerup==='megaciak'?'#ff6600':'#ffd700';
    ctx.fillStyle=ctx.shadowColor;ctx.beginPath();ctx.arc(0,0,14,0,Math.PI*2);ctx.fill();
    ctx.shadowBlur=0;
  }

  ctx.globalAlpha=1;ctx.restore();
}

// ========== SCORE & RANK ==========
export function calcFinalScore(g){
  const lv=g.level;
  const completion=g.completed?200:0;
  const timeBonus=g.completed?Math.max(0,Math.round(g.time*1.5)):0;
  const starPts=g.stars*5;
  const dmgPen=g.damage*15;
  const secretPts=g.secretsFound*50;
  return clamp(Math.round(completion+timeBonus+starPts-dmgPen+secretPts),0,999);
}

export function calcRank(score){
  if(score>=850)return'LEGENDARY DIRECTOR';if(score>=750)return'S+';if(score>=650)return'S';
  if(score>=500)return'A';if(score>=350)return'B';if(score>=200)return'C';return'D';
}

export function rankColor(rank){
  if(rank==='LEGENDARY DIRECTOR')return'#ffd700';if(rank==='S+'||rank==='S')return'#ff00ff';
  if(rank==='A')return'#00ff66';if(rank==='B')return'#00aaff';if(rank==='C')return'#ffaa00';return'#888';
}
