(() => {
  const el = id => document.getElementById(id);
  const ns = 'http://www.w3.org/2000/svg';
  const svg = (tag, attrs, text) => {
    const node=document.createElementNS(ns,tag);
    Object.entries(attrs).forEach(([key,value])=>node.setAttribute(key,String(value)));
    if(text!==undefined)node.textContent=text;
    return node;
  };
  let datasets=[], active=null, time=0, running=false, frame=0, previous=0, valid=false;
  let people=new Map(), stations=[];
  const reduced=matchMedia('(prefers-reduced-motion: reduce)');
  function pause() {
    running=false;cancelAnimationFrame(frame);el('replay-stage').classList.add('paused');
    el('replay-play').textContent='▶ Continuar';el('replay-status').textContent='Pausado';
  }
  function select() {
    pause();active=datasets[Number(el('replay-source').value)];
    if(!active)return;
    time=0;people=new Map();stations=[];
    el('replay-people').replaceChildren();layout();
    el('replay-time').max=String(Math.max(active.horizon,...active.jobs.map(j=>j.end+0.6)));
    el('replay-description').textContent=active.description;
    el('replay-play').textContent='▶ Iniciar';el('replay-status').textContent='Pronto para reproduzir';draw();
  }
  function layout() {
    const room=el('replay-room');room.replaceChildren();stations=[];
    const columns=el('replay-stage').parentElement.clientWidth>=900?3:2;
    active.columns=columns;
    const normalRows=Math.ceil(active.normalCount/columns);
    const autoRows=Math.ceil((active.labels.length-active.normalCount)/columns);
    const autoTop=75+normalRows*78+(normalRows?42:0);
    active.height=Math.max(400,autoTop+autoRows*78+42);
    active.width=columns===3?1120:900;
    el('replay-stage').setAttribute('viewBox',`0 0 ${active.width} ${active.height}`);
    room.append(svg('rect',{x:45,y:65,width:255,height:active.height-105,rx:18,fill:'#e1e9da'}),
      svg('text',{x:25,y:32,class:'room-label'},'ENTRADA'),svg('text',{x:100,y:52,class:'room-label'},'FILA DE ESPERA'),
      svg('text',{x:355,y:32,class:'room-label'},'ATENDIMENTO'),svg('text',{x:active.width-65,y:32,class:'room-label'},'SAÍDA'));
    if(active.normalCount)room.append(svg('text',{x:355,y:60,class:'room-label'},'CAIXAS CONVENCIONAIS'));
    if(autoRows)room.append(svg('text',{x:355,y:autoTop-12,class:'room-label'},'AUTOATENDIMENTO'));
    active.positions=active.labels.map((name,index)=>{
      const machine=index>=active.normalCount;
      const local=machine?index-active.normalCount:index;
      const x=350+(local%columns)*235,y=(machine?autoTop:75)+Math.floor(local/columns)*78;
      room.append(svg('rect',{x:x+25,y,width:155,height:53,rx:9,fill:'#fff',stroke:'#c6d4c0'}),svg('text',{x:x+35,y:y+21,class:'station-label'},name));
      const label=svg('text',{x:x+35,y:y+40,class:'station-state'},'Disponível');room.append(label);stations.push(label);
      if(machine){
        room.append(svg('rect',{x:x+189,y:y+3,width:22,height:31,rx:3,fill:'#31586c'}),svg('rect',{x:x+192,y:y+7,width:16,height:14,rx:2,fill:'#b9e1e6'}),svg('path',{d:`M${x+200} ${y+34} v12 m-8 0 h16`,stroke:'#31586c','stroke-width':3}));
      }else{
        room.append(svg('circle',{cx:x+200,cy:y+12,r:6,fill:'#6e8c62'}),svg('path',{d:`M${x+192} ${y+22} q8 -7 16 0 v18 h-16 Z`,fill:'#6e8c62'}));
      }
      return {x:x+8,y:y+25};
    });
  }
  function draw() {
    if(!active)return;
    const waiting=active.jobs.filter(j=>j.arrival<=time && time<j.start);
    const serving=active.jobs.filter(j=>j.start<=time && time<j.end);
    const done=active.jobs.filter(j=>j.end<=time).length;
    el('replay-waiting').textContent=waiting.length;
    el('replay-serving').textContent=serving.length;
    el('replay-done').textContent=done;
    el('replay-time').value=time;
    el('replay-clock').textContent=new Date(active.base+time*60000).toLocaleTimeString('pt-BR',{hour:'2-digit',minute:'2-digit',second:'2-digit'});
    stations.forEach((label,i)=>{label.textContent=serving.some(j=>j.station===i)?'Em atendimento':'Disponível';});
    const visibleWaiting=Math.min(30,Math.floor((active.height-135)/64)*5);
    const visible=[...waiting.slice(0,visibleWaiting),...serving,...active.jobs.filter(j=>j.end<=time && time<j.end+0.6).slice(-20)];
    const ids=new Set(visible.map(j=>j.id));
    people.forEach((node,id)=>{if(!ids.has(id)){node.remove();people.delete(id);}});
    visible.forEach(job=>{
      let person=people.get(job.id);
      if(!person){
        person=svg('g',{class:'person'});
        person.append(svg('title',{},job.id),svg('circle',{class:'head',cx:0,cy:-17,r:7}),
          svg('path',{class:'body',d:'M-6 -7 Q0 -12 6 -7 L9 10 L5 10 L5 25 L1 25 L0 12 L-1 25 L-5 25 L-5 10 L-9 10 Z'}),
          svg('text',{class:'person-id',x:0,y:39},job.id));
        person.style.transform=`translate(30px, 95px)`;
        el('replay-people').append(person);people.set(job.id,person);
      }
      let x,y;
      const rank=waiting.indexOf(job);
      if(time>=job.end){x=active.width-35;y=active.positions[job.station].y;person.setAttribute('class','person departing');}
      else if(time>=job.start){x=active.positions[job.station].x;y=active.positions[job.station].y;person.setAttribute('class','person serving');}
      else {x=270-(rank%5)*47;y=95+Math.floor(rank/5)*64;person.setAttribute('class','person');}
      person.style.transform=`translate(${x}px, ${y}px)`;
    });
    let extra=el('replay-overflow');
    if(!extra){extra=svg('text',{id:'replay-overflow',x:55,y:heightForOverflow(),class:'station-label'});el('replay-room').append(extra);}
    extra.textContent=waiting.length>visibleWaiting?`+ ${waiting.length-visibleWaiting} aguardando`:'';
  }
  function heightForOverflow(){return active.height-15;}
  function tick(now) {
    if(!running)return;
    const dt=Math.min(0.25,(now-previous)/1000);previous=now;
    time=Math.min(Number(el('replay-time').max),time+dt*Number(el('replay-speed').value));draw();
    if(time>=Number(el('replay-time').max)){pause();el('replay-play').textContent='↻ Reproduzir novamente';el('replay-status').textContent='Reprodução concluída';return;}
    frame=requestAnimationFrame(tick);
  }
  el('replay-play').onclick=()=>{
    if(!valid)return;
    if(running){pause();return;}
    if(time>=Number(el('replay-time').max))time=0;
    running=true;previous=performance.now();el('replay-stage').classList.remove('paused');
    el('replay-play').textContent='Ⅱ Pausar';el('replay-status').textContent=reduced.matches?'Reproduzindo com movimento reduzido':'Reproduzindo';frame=requestAnimationFrame(tick);
  };
  new ResizeObserver(()=>{
    if(active && (el('replay-stage').parentElement.clientWidth>=900?3:2)!==active.columns){layout();draw();}
  }).observe(el('replay-stage').parentElement);
  el('replay-reset').onclick=select;
  el('replay-source').onchange=select;
  el('replay-time').oninput=()=>{pause();time=Number(el('replay-time').value);draw();};
  document.addEventListener('visibilitychange',()=>{if(document.hidden&&running)pause();});
  document.addEventListener('replay-invalid',()=>{
    pause();valid=false;['replay-play','replay-reset','replay-source','replay-time'].forEach(id=>el(id).disabled=true);
    el('replay-status').textContent='Calcule os dados para atualizar a reprodução';
  });
  document.addEventListener('replay-ready',event=>{
    const {result,start,cashiers}=event.detail;
    const base=new Date(start).getTime();
    const configuration=result.configuration;
    const labels=[...Array.from({length:configuration.normal_cashiers},(_,i)=>`Caixa ${i+1}`),...Array.from({length:configuration.self_cashiers},(_,i)=>`Totem ${i+1}`)];
    datasets=[{base,horizon:result.observed.duration_min,labels,normalCount:configuration.normal_cashiers,
      description:'Projeção da configuração: mesmas chegadas, durações e tipos do CSV; o aplicativo distribui as pessoas entre todos os postos disponíveis do tipo escolhido.',
      jobs:result.scenarios[0].projection.timeline},
      ...result.scenarios.map(c=>({base,horizon:result.observed.duration_min,labels:[...Array.from({length:c.normal_cashiers},(_,i)=>`Caixa ${i+1}`),...Array.from({length:c.self_cashiers},(_,i)=>`Totem ${i+1}`)],normalCount:c.normal_cashiers,jobs:c.simulation.timeline,
        description:`${c.name} · execução 1 de 30 · semente ${result.seed} · chegadas Poisson, tipos nas proporções observadas e serviços reamostrados. Postos redistribuídos.`}))];
    el('replay-source').replaceChildren(...datasets.map((data,i)=>{const o=document.createElement('option');o.value=i;o.textContent=i===0?'Projeção da configuração':`Simular: ${result.scenarios[i-1].name}`;return o;}));
    valid=true;['replay-play','replay-reset','replay-source','replay-time'].forEach(id=>el(id).disabled=false);select();
  });
})();
