const $ = (selector) => document.querySelector(selector);
const state = {result: null, dirty: false, busy: false, dataUnsaved: false, emptyCollection: false};
const nf = new Intl.NumberFormat('pt-BR', {maximumFractionDigits: 2});
const fmt = (value) => value === null || value === undefined ? '—' : nf.format(value);
const pct = (value) => value == null ? '—' : `${fmt(value * 100)}%`;
const esc = (value) => String(value).replace(/[&<>"']/g, (char) => ({'&':'&amp;', '<':'&lt;', '>':'&gt;', '"':'&quot;', "'":'&#39;'}[char]));
const fields = ['id','chegada','inicio_atendimento','fim_atendimento','caixa','fila','origem','observacoes','estabelecimento','tipo_caixa','itens','inicio_observacao','fim_observacao','capacidade_convencional','capacidade_autoatendimento'];

function notice(message, error = false) {
  $('#notice').textContent = message;
  $('#notice').classList.toggle('error', error);
}

function dirty() {
  document.dispatchEvent(new Event('replay-invalid')); 
  state.dirty = true;
  $('#export-results').disabled = true;
  notice('Há alterações pendentes. Clique em “Calcular e comparar” para atualizar os resultados.');
}

function csvCell(value) {
  // Exporta apenas texto literal: evita fórmulas ao abrir observações no Excel.
  let text = String(value ?? '');
  if (typeof value === 'string' && /^[=+@\-\t\r]/.test(text)) text = "'" + text;
  return `"${text.replaceAll('"','""')}"`;
}

function makeCSV(rows, keys = fields) {
  return keys.map(csvCell).join(';') + '\r\n' + rows.map(row => keys.map(key => csvCell(row[key])).join(';')).join('\r\n') + '\r\n';
}

function download(text, name) {
  const url = URL.createObjectURL(new Blob(['\ufeff', text], {type:'text/csv;charset=utf-8'}));
  const link = document.createElement('a');
  link.href = url; link.download = name; link.click();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}

function confirmReplace(message) {
  return new Promise(resolve => {
    const dialog=document.createElement('dialog');
    dialog.className='confirm-dialog';
    dialog.setAttribute('aria-label','Confirmar substituição dos dados');
    const text=document.createElement('p');text.textContent=message;
    const cancel=document.createElement('button');cancel.className='button secondary';cancel.textContent='Cancelar';
    const accept=document.createElement('button');accept.className='button primary';accept.textContent='Substituir dados';
    const finish=value=>{dialog.close();dialog.remove();resolve(value);};
    cancel.onclick=()=>finish(false);accept.onclick=()=>finish(true);
    dialog.addEventListener('cancel',event=>{event.preventDefault();finish(false);});
    const actions=document.createElement('div');actions.className='button-group';actions.append(cancel,accept);
    dialog.append(text,actions);document.body.append(dialog);dialog.showModal();cancel.focus();
  });
}

function addScenario({name = 'Novo cenário', demand = 0, service = 0, cashiers = Number($('#normal-cashiers').value), automatic = Number($('#self-cashiers').value)} = {}) {
  if ($$('.scenario-card').length >= 7) return notice('Limite de sete cenários alternativos.', true);
  const card = document.createElement('article');
  card.className = 'scenario-card';
  card.innerHTML = `<div class="scenario-head"><input class="scenario-name" aria-label="Nome do cenário" maxlength="60" required value="${esc(name)}"><button class="remove" type="button" aria-label="Excluir cenário">Excluir ×</button></div><div class="scenario-fields"><label>Demanda (%)<input data-field="demand" type="number" min="-80" max="200" step="1" value="${esc(demand)}"></label><label>Duração do serviço (%)<input data-field="service" type="number" min="-80" max="200" step="1" value="${esc(service)}"></label><label>Convencionais<input data-field="cashiers" type="number" min="0" max="20" step="1" value="${esc(cashiers)}"></label><label>Autoatendimento<input data-field="automatic" type="number" min="0" max="20" step="1" value="${esc(automatic)}"></label></div><div class="scenario-shortcuts"><button type="button" class="shortcut" data-shortcut="demand">Demanda +20%</button><button type="button" class="shortcut" data-shortcut="cashier">+1 posto</button><button type="button" class="shortcut" data-shortcut="service">Serviço −10%</button></div>`;
  card.querySelector('.remove').onclick = () => {card.remove(); dirty();};
  card.querySelectorAll('[data-shortcut]').forEach(button => button.onclick = () => {
    const kind = button.dataset.shortcut;
    const input = card.querySelector(`[data-field="${kind === 'cashier' ? 'cashiers' : kind}"]`);
    input.value = kind === 'cashier' ? Math.min(20, Number(input.value) + 1) : kind === 'demand' ? 20 : -10;
    dirty();
  });
  card.addEventListener('input', dirty);
  $('#scenario-list').append(card);
  dirty();
}

function $$(selector) {return [...document.querySelectorAll(selector)];}

function numericInput(input) {
  if (!input.reportValidity() || !input.value.trim()) throw new Error('Preencha os campos numéricos e respeite os limites indicados.');
  return Number(input.value);
}

function payload(csvOverride) {
  const scenarios = $$('.scenario-card').map(card => ({
    name: card.querySelector('.scenario-name').value.trim(),
    demand_pct: numericInput(card.querySelector('[data-field="demand"]')),
    service_pct: numericInput(card.querySelector('[data-field="service"]')),
    normal_cashiers: numericInput(card.querySelector('[data-field="cashiers"]')),
    self_cashiers: numericInput(card.querySelector('[data-field="automatic"]')),
    cashiers: Number(card.querySelector('[data-field="cashiers"]').value)+Number(card.querySelector('[data-field="automatic"]').value),
  }));
  return {csv: csvOverride ?? $('#csv-text').value, start: $('#start').value, end: $('#end').value,
    cashiers: Number($('#normal-cashiers').value)+Number($('#self-cashiers').value),
    normal_cashiers:numericInput($('#normal-cashiers')), self_cashiers:numericInput($('#self-cashiers')),
    station_types:Object.fromEntries($$('#station-mapping select').map(input=>[input.dataset.station,input.value])),
    self_service_ratio:$('#self-ratio').value.trim()?numericInput($('#self-ratio')):null, seed: numericInput($('#seed')), scenarios};
}

async function calculate(csvOverride) {
  if (state.busy) return false;
  state.busy = true;
  const controls = $$('button,input,textarea,select,summary');
  const previous = controls.map(control => control.disabled);
  try {
    const data = payload(csvOverride);
    controls.forEach(control => control.disabled = true);
    notice('Calculando indicadores e executando 30 simulações por cenário…');
    const response = await fetch('/api/analisar', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify(data)});
    const result = await response.json();
    if (!response.ok) throw new Error(result.error || 'Falha ao analisar os dados.');
    if (csvOverride !== undefined) $('#csv-text').value = csvOverride;
    state.result = result; state.dirty = false; state.emptyCollection = false;
    $('#setup-screen').hidden=true;$('#dashboard').hidden=false;
    document.body.classList.remove('import-step','config-step');document.body.classList.add('analysis-ready');
    render(result);
    notice(`${result.observed.records} registros analisados. Resultados atualizados com a semente ${result.seed}.`);
    return true;
  } catch (error) {
    state.dirty = true;
    notice(`${error.message} Os resultados exibidos, se houver, são da última análise válida.`, true);
    $('#notice').scrollIntoView({block:'center'});
    return false;
  } finally {
    controls.forEach((control, index) => control.disabled = previous[index]);
    $('#export-results').disabled = state.dirty || !state.result;
    state.busy = false;
    if (!state.dirty && state.result) document.dispatchEvent(new CustomEvent('replay-ready', {detail:{result:state.result,start:$('#start').value,cashiers:Number($('#cashiers').value)}}));
  }
}

function render(result) {
  const o = result.observed;
  const projection=result.scenarios[0].projection;
  const difference=o.wait_min-projection.wait_min;
  const waitChange=Math.abs(difference)<0.005?'Sem alteração na espera':`${difference>0?'Redução':'Aumento'} de ${fmt(Math.abs(difference))} min${o.wait_min>0?` (${fmt(Math.abs(difference)/o.wait_min*100)}%)`:''}`;
  $('#decision-summary').textContent=`Espera observada: ${fmt(o.wait_min)} min → com ${result.configuration.normal_cashiers} convencionais e ${result.configuration.self_cashiers} totens: ${fmt(projection.wait_min)} min. ${difference>=0?'Redução':'Aumento'} de ${fmt(Math.abs(difference))} min. Projeção com as mesmas chegadas, durações e tipos do CSV; postos redistribuídos.`;
  const names = [...new Set(result.rows.map(row=>row.estabelecimento).filter(Boolean))];
  $('#operation-name').textContent = names.length === 1 ? names[0] : names.length > 1 ? 'Múltiplas operações' : 'Operação sem nome';
  const metrics = [
    ['Espera média projetada',projection.wait_min,'min',`${waitChange} · Coleta: ${fmt(o.wait_min)} min`],
    ['Fila média projetada',projection.queue_mean,'clientes',`Coleta: ${fmt(o.queue_mean)} clientes · média durante a janela`],
    ['Tempo médio no sistema',projection.system_min,'min',`Espera + atendimento · Coleta: ${fmt(o.system_min)} min`],
    ['Atendimentos concluídos',projection.completed,'clientes',`Dentro da janela · Coleta: ${fmt(o.completed)} clientes`],
  ];
  $('#metrics').innerHTML = metrics.map((m,i) => `<article class="metric ${i===0?'featured':''}"><div class="metric-label">${m[0]}</div><div class="metric-value">${fmt(m[1])}<span>${m[2]}</span></div><div class="metric-note">${m[3]}</div></article>`).join('');
  const maximum = Math.max(1,...o.bins.map(bin => bin.count));
  const start = new Date($('#start').value);
  const timeAt = minutes => new Date(start.getTime()+minutes*60000).toLocaleTimeString('pt-BR',{hour:'2-digit',minute:'2-digit'});
  const chart = $('#arrival-chart');
  // CSSOM mantém alturas dinâmicas sem relaxar a política de conteúdo da página.
  chart.replaceChildren();
  const showEvery = Math.max(1, Math.ceil(o.bins.length / 10));
  o.bins.forEach((bin,index) => {
    const column = document.createElement('div'); column.className='chart-column';
    column.title=`${timeAt(bin.minute)}: ${bin.count} chegadas`;
    column.innerHTML=`<span class="chart-number">${bin.count}</span><div class="chart-bar"></div><span class="chart-time">${index % showEvery === 0 ? timeAt(bin.minute) : ''}</span>`;
    column.querySelector('.chart-bar').style.height=`${bin.count/maximum*105}px`;
    chart.append(column);
  });
  chart.setAttribute('aria-label',o.bins.map(bin => `${timeAt(bin.minute)}: ${bin.count} chegadas`).join('; '));
  $('#period-caption').textContent = `${timeAt(0)} a ${timeAt(o.duration_min)} · ${fmt(o.duration_min)} minutos de observação · último intervalo pode ser parcial`;
  $('#operation-details').innerHTML = [['Caixas convencionais',result.configuration.normal_cashiers],['Autoatendimento',result.configuration.self_cashiers],['Tempo médio no sistema',`${fmt(o.system_min)} min`],['Maior fila observada',`${o.queue_max} clientes`],['Pessoas no início da janela',o.initial_system],['Pessoas restantes no fim',o.remaining]].map(([key,value]) => `<div><dt>${key}</dt><dd>${esc(value)}</dd></div>`).join('');
  $('#comparison-body').innerHTML = result.scenarios.map((case_,i) => {
    const sim = case_.simulation, t=case_.theory;
    return `<tr><td>${esc(case_.name)}<small>${case_.normal_cashiers} convencionais + ${case_.self_cashiers} totens · ${fmt(case_.arrival_hour)} chegadas/h</small></td><td>${fmt(case_.projection.wait_min)} min<small>Mesmas chegadas e durações</small></td><td>${fmt(sim.wait_min)} min<small>± ${fmt(sim.wait_sd_min)} min entre execuções</small></td><td>${fmt(sim.queue_mean)} clientes</td><td>${pct(sim.utilization)}</td><td>${fmt(sim.completed)}<small>Média das repetições</small></td><td class="${t.stable?'':'overload'}">${t.stable===null?'Não aplicável':t.stable?`${fmt(t.wait_min)} min`:'Sobrecarga'}<small>${t.stable===null?'Tipos de posto diferentes':t.stable?'Hipóteses ainda não verificadas':'Sem média estacionária finita'}</small></td></tr>`;
  }).join('');
  $('#comparison-note').textContent = `Na coleta, a espera média foi ${fmt(o.wait_min)} min; na simulação da configuração atual, ${fmt(result.scenarios[0].simulation.wait_min)} min. A simulação começa vazia e usa chegadas Poisson constantes. Diferenças precisam ser investigadas antes de recomendar mudanças à operação.`;
  $('#data-count').textContent=`${o.records} registros completos · ${o.count} chegadas dentro da janela · ${o.completed} saídas dentro da janela`;
  const shortTime = value => value.slice(11,19);
  $('#records-body').innerHTML=result.rows.map(row => `<tr><td>${esc(row.id)}</td><td title="${esc(row.chegada)}">${esc(shortTime(row.chegada))}</td><td title="${esc(row.inicio_atendimento)}">${esc(shortTime(row.inicio_atendimento))}</td><td title="${esc(row.fim_atendimento)}">${esc(shortTime(row.fim_atendimento))}</td><td>${esc(row.caixa)}</td><td>${fmt((new Date(row.inicio_atendimento.replace(' ','T'))-new Date(row.chegada.replace(' ','T')))/60000)} min</td><td>${['FICTICIO','SINTETICO'].includes(row.origem)?'Teste gerado':esc(row.origem || 'Não informada')}</td></tr>`).join('');
  $('#warnings').innerHTML=o.warnings.map(text=>`<li>${esc(text)}</li>`).join('');
}

function previewSetup() {
  const n=Number($('#normal-cashiers').value),a=Number($('#self-cashiers').value);
  $('#cashiers').value=n+a;
  const types=$$('#station-mapping select').map(input=>input.value);
  const missing=(n>0&&!types.includes('normal'))||(a>0&&!types.includes('self'));
  $('#self-ratio').required=missing;
  if(missing) $('.setup-options').open=true;
  const icons={
    person:'<svg viewBox="0 0 28 46" aria-hidden="true" focusable="false"><circle cx="14" cy="9" r="6" fill="#6e8c62"/><path d="M6 19 q8 -7 16 0 v18 H6 Z" fill="#6e8c62"/></svg>',
    machine:'<svg viewBox="0 0 28 46" aria-hidden="true" focusable="false"><rect x="3" y="2" width="22" height="31" rx="3" fill="#31586c"/><rect x="6" y="6" width="16" height="14" rx="2" fill="#b9e1e6"/><path d="M14 33 v11 m-8 0 h16" stroke="#31586c" stroke-width="3"/></svg>'
  };
  $('#setup-layout').innerHTML=[['Caixas convencionais',n,'person','normal'],['Autoatendimento',a,'machine','self']].map(([name,count,icon,type])=>`<div class="layout-group"><p><span>${name}</span><span class="layout-total"><strong>${count}</strong><span class="post-adjusters" aria-label="Ajustar quantidade de ${name.toLowerCase()}"><button type="button" class="post-adjuster" data-post-type="${type}" data-change="-1" aria-label="Remover ${name.toLowerCase()}" ${n+a<=1||count<=0?'disabled':''}>−</button><button type="button" class="post-adjuster add" data-post-type="${type}" data-change="1" aria-label="Adicionar ${name.toLowerCase()}" ${n+a>=20?'disabled':''}>+</button></span></span></p><div class="layout-posts">${Array.from({length:Math.min(20,Math.max(0,Math.floor(count)))},(_,i)=>`<span class="layout-post ${icon==='machine'?'machine':''}">${icons[icon]}${i+1}</span>`).join('')||'<span class="muted small">Nenhum configurado</span>'}</div></div>`).join('');
}
$('#setup-form').onsubmit=async event=>{
  event.preventDefault();previewSetup();
  if(await calculate()) {$('#visao').scrollIntoView();}
};
$('#edit-config').onclick=()=>{
  document.dispatchEvent(new Event('replay-invalid'));
  $('#dashboard').hidden=true;$('#setup-screen').hidden=false;
  document.body.classList.remove('analysis-ready');document.body.classList.add('config-step');
  window.scrollTo(0,0);previewSetup();
};
$('#replace-file').onclick=()=>$('#csv-file').click();
$('#run').onclick=()=>calculate();
$('#add-scenario').onclick=()=>addScenario();
['#start','#end','#normal-cashiers','#self-cashiers','#self-ratio','#seed','#csv-text'].forEach(selector=>$(selector).addEventListener('input',()=>{dirty();previewSetup();}));
$('#setup-layout').addEventListener('click',event=>{
  const button=event.target.closest('.post-adjuster');if(!button||button.disabled)return;
  const input=$(button.dataset.postType==='normal'?'#normal-cashiers':'#self-cashiers');
  const other=$(button.dataset.postType==='normal'?'#self-cashiers':'#normal-cashiers');
  const next=Math.max(0,Math.min(20,Number(input.value)+Number(button.dataset.change)));
  if(next+Number(other.value)<1||next+Number(other.value)>20)return;
  input.value=next;dirty();previewSetup();input.focus();
});
$('#csv-text').addEventListener('input',()=>{state.dataUnsaved=true;state.emptyCollection=false;});
$('#csv-file').onchange=async event=>{
  const file=event.target.files[0];if(!file)return;
  try {
    if(file.size>1_500_000)throw new Error('Use um CSV de até 1,5 MB.');
    if(state.dataUnsaved&&!await confirmReplace('Substituir a coleta desta página? Exporte suas alterações se precisar guardá-las.'))return;
    const text=await file.text();
    const response=await fetch('/api/inspecionar',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({csv:text})});
    const inspection=await response.json();if(!response.ok)throw new Error(inspection.error);
    state.result=null;state.dirty=false;state.dataUnsaved=false;
    document.dispatchEvent(new Event('replay-invalid'));
    $('#csv-text').value=text;$('#file-name').textContent=file.name;
    $('#setup-file').textContent=`${file.name} · ${inspection.records} registros · ${inspection.stations.length} postos identificados`;
    const declared=inspection.station_types || {};
    $('#normal-cashiers').value=inspection.normal_cashiers ?? inspection.stations.filter(id=>(declared[id]||'normal')==='normal').length;
    $('#self-cashiers').value=inspection.self_cashiers ?? inspection.stations.filter(id=>declared[id]==='self').length;$('#self-ratio').value='';
    $('#start').value=inspection.first_arrival;
    const last=new Date(inspection.last_arrival);last.setMinutes(last.getMinutes()+1);
    $('#end').value=last.getFullYear()+'-'+String(last.getMonth()+1).padStart(2,'0')+'-'+String(last.getDate()).padStart(2,'0')+'T'+String(last.getHours()).padStart(2,'0')+':'+String(last.getMinutes()).padStart(2,'0')+':'+String(last.getSeconds()).padStart(2,'0');
    if(inspection.observation_start && inspection.observation_end){
      $('#start').value=inspection.observation_start.replace(' ','T');$('#end').value=inspection.observation_end.replace(' ','T');
      $('#window-hint').textContent='Período declarado no CSV. Confira se corresponde à janela usada na coleta ou no teste.';
    }else $('#window-hint').textContent='Horários sugeridos a partir das chegadas. Corrija para o início e fim reais da coleta.';
    $('#station-mapping').replaceChildren(...inspection.stations.map(id=>{
      const label=document.createElement('label');label.className='station-map';label.append(document.createTextNode(id));
      const select=document.createElement('select');select.dataset.station=id;
      [['normal','Convencional (com atendente)'],['self','Autoatendimento (totem)']].forEach(([value,text])=>{const option=document.createElement('option');option.value=value;option.textContent=text;select.append(option);});
      select.value=declared[id]||'normal';
      select.onchange=()=>{dirty();previewSetup();};label.append(select);return label;
    }));
    $('#scenario-list').replaceChildren();$('#import-screen').hidden=true;$('#setup-screen').hidden=false;$('#dashboard').hidden=true;
    document.body.classList.remove('import-step','analysis-ready');document.body.classList.add('config-step');
    previewSetup();notice('CSV validado. Confira o período real, a capacidade e o tipo de cada posto antes de analisar.');window.scrollTo(0,0);
  }catch(error){notice(error.message,true);}finally{event.target.value='';}
};

$('#manual-form').onsubmit = async event => {
  event.preventDefault();
  if(state.busy) return;
  if(!state.emptyCollection && (state.dirty || !state.result)) return notice('Calcule primeiro as alterações pendentes da coleta e dos cenários; depois adicione o atendimento.',true);
  const form = event.target;
  const row=Object.fromEntries(new FormData(form));
  ['chegada','inicio_atendimento','fim_atendimento'].forEach(key => {row[key]=row[key].replace('T',' ');if(row[key].length===16)row[key]+=':00';});
  const text=makeCSV([...(state.emptyCollection ? [] : state.result.rows),row]);
  if(await calculate(text)) {state.dataUnsaved=true;form.reset();$('#file-name').textContent='Coleta editada — exporte para guardar';}
};
$('#export-data').onclick = () => {download($('#csv-text').value,'coleta_atendimentos.csv');};
$('#export-results').onclick = () => {
  if(!state.result || state.dirty)return;
  const result=state.result;
  const rows=result.scenarios.map(c=>({cenario:c.name,origem_dados:result.observed.source,inicio_observacao:$('#start').value,fim_chegadas:$('#end').value,semente:result.seed,repeticoes:c.simulation.repetitions,caixas:c.cashiers,convencionais:c.normal_cashiers,autoatendimento:c.self_cashiers,hipotese_duracao_totem_pct:result.configuration.self_service_ratio,demanda_pct:c.demand_pct,duracao_pct:c.service_pct,espera_redistribuida_min:c.projection.wait_min,espera_observada_min:result.observed.wait_min,espera_sim_min:c.simulation.wait_min,dp_espera_sim_min:c.simulation.wait_sd_min,fila_sim_media:c.simulation.queue_mean,ocupacao_sim:c.simulation.utilization,concluidos_sim:c.simulation.completed,espera_teorica_min:c.theory.wait_min,teoria_estavel:c.theory.stable}));
  download(makeCSV(rows,Object.keys(rows[0])),'comparacao_cenarios.csv');
};
window.addEventListener('beforeunload',event=>{if(state.dirty || state.dataUnsaved || (state.result && state.result.observed.source === 'REAL')){event.preventDefault();event.returnValue='';}});
$$('nav a').forEach(a=>a.addEventListener('click',()=>{$$('nav a').forEach(link=>link.classList.remove('active'));a.classList.add('active');}));
$('nav a').classList.add('active');

