"""Cálculos em minutos; datas são horários locais, sem conversão de fuso."""

import csv
import heapq
import io
import math
import random
import statistics
from datetime import datetime


FIELDS = ['id', 'chegada', 'inicio_atendimento', 'fim_atendimento', 'caixa', 'fila', 'origem', 'observacoes', 'estabelecimento', 'tipo_caixa', 'itens', 'inicio_observacao', 'fim_observacao', 'capacidade_convencional', 'capacidade_autoatendimento']


def timestamp(value):
    try:
        result = datetime.fromisoformat(str(value).strip())
        if result.tzinfo is not None:
            raise ValueError()
        return result
    except (ValueError, TypeError):
        raise ValueError('Use data e hora local no formato AAAA-MM-DD HH:MM:SS, sem fuso.') from None


def number(value, label, low, high, integer=False):
    if isinstance(value, bool):
        raise ValueError(f'{label}: valor inválido.')
    try:
        result = float(value)
    except (ValueError, TypeError):
        raise ValueError(f'{label}: informe um número.') from None
    if not math.isfinite(result) or not low <= result <= high or (integer and result != int(result)):
        raise ValueError(f'{label}: use um valor entre {low} e {high}' + (' inteiro.' if integer else '.'))
    return int(result) if integer else result


def parse_csv(text):
    if not isinstance(text, str) or len(text) > 1_500_000:
        raise ValueError('CSV inválido ou muito grande (máximo 1,5 MB).')
    try:
        dialect = csv.Sniffer().sniff(text[:4096].lstrip('\ufeff'), delimiters=',;\t')
        reader = csv.DictReader(io.StringIO(text.lstrip('\ufeff')), dialect=dialect)
        if not reader.fieldnames or not set(FIELDS[:6]).issubset(reader.fieldnames):
            raise ValueError('Cabeçalho obrigatório: ' + ', '.join(FIELDS[:6]))
        rows = []
        ids = set()
        for line, raw in enumerate(reader, 2):
            if line > 5001:
                raise ValueError('Limite de 5.000 registros por coleta.')
            if None in raw or any(raw.get(key) is None for key in FIELDS[:6]):
                raise ValueError(f'Linha {line}: quantidade de campos incorreta.')
            row = {key: (raw.get(key) or '').strip() for key in FIELDS}
            if any(len(value) > 500 for value in row.values()):
                raise ValueError(f'Linha {line}: campo com mais de 500 caracteres.')
            if not row['id'] or row['id'] in ids:
                raise ValueError(f'Linha {line}: identificador vazio ou duplicado.')
            if not row['caixa'] or not row['fila']:
                raise ValueError(f'Linha {line}: informe caixa e fila.')
            ids.add(row['id'])
            a, s, e = (timestamp(row[key]) for key in FIELDS[1:4])
            if not a <= s < e:
                raise ValueError(f'Linha {line}: chegada ≤ início < fim é obrigatório; não preencha tempos desconhecidos com zero.')
            row.update(a=a, s=s, e=e)
            rows.append(row)
    except csv.Error:
        raise ValueError('Não foi possível ler o CSV. Verifique separadores e aspas.') from None
    if not rows:
        raise ValueError('Adicione pelo menos um atendimento completo.')
    if len({r['fila'] for r in rows}) != 1:
        raise ValueError('Esta versão analisa uma fila única. Separe filas independentes em coletas distintas.')
    for cashier in {r['caixa'] for r in rows}:
        if cashier in ('C', 'CA'):
            continue  # C/CA são tipos com vários postos, não identificadores físicos.
        services = sorted((r['s'], r['e']) for r in rows if r['caixa'] == cashier)
        if any(current[0] < previous[1] for previous, current in zip(services, services[1:])):
            raise ValueError(f'{cashier}: há atendimentos sobrepostos. Revise os horários.')
    return sorted(rows, key=lambda r: (r['a'], r['id']))


def area(left, right, start, end):
    return max(0.0, (min(right, end) - max(left, start)).total_seconds() / 60)


def inspect_data(payload):
    if not isinstance(payload, dict):
        raise ValueError('Requisição inválida.')
    rows = parse_csv(payload.get('csv'))
    declared = {}
    for row in rows:
        kind = row['tipo_caixa'] or {'C': 'normal', 'CA': 'self'}.get(row['caixa'], '')
        if kind:
            if kind not in ('normal','self') or (row['caixa'] in declared and declared[row['caixa']] != kind):
                raise ValueError('tipo_caixa deve ser normal ou self, consistente por posto.')
            declared[row['caixa']] = kind
    starts = {r['inicio_observacao'] for r in rows if r['inicio_observacao']}
    ends = {r['fim_observacao'] for r in rows if r['fim_observacao']}
    observation_start = next(iter(starts)) if len(starts) == 1 else None
    observation_end = next(iter(ends)) if len(ends) == 1 else None
    if observation_start and observation_end and timestamp(observation_start) >= timestamp(observation_end):
        raise ValueError('Janela declarada inválida.')
    capacity = {}
    for key, target in [('capacidade_convencional','normal_cashiers'),('capacidade_autoatendimento','self_cashiers')]:
        values = {r[key] for r in rows if r[key]}
        if len(values) == 1:
            capacity[target] = number(next(iter(values)), key, 0, 20, True)
    return {**capacity, 'station_types': declared, 'observation_start': observation_start, 'observation_end': observation_end,
            'stations': sorted({r['caixa'] for r in rows}), 'records': len(rows),
            'first_arrival': min(r['a'] for r in rows).isoformat(),
            'last_arrival': max(r['a'] for r in rows).isoformat(),
            'names': sorted({r['estabelecimento'] for r in rows if r['estabelecimento']})}


def observed(rows, start, end, cashiers):
    duration = (end - start).total_seconds() / 60
    if not 0 < duration <= 720:
        raise ValueError('O período deve ser positivo e ter no máximo 12 horas.')
    relevant = [r for r in rows if r['a'] < end and r['e'] > start]
    cohort = [r for r in rows if start <= r['a'] < end]
    if not cohort:
        raise ValueError('Não há chegadas dentro do período de observação.')
    service = [(r['e'] - r['s']).total_seconds() / 60 for r in relevant]
    waits = [(r['s'] - r['a']).total_seconds() / 60 for r in cohort]
    system = [(r['e'] - r['a']).total_seconds() / 60 for r in cohort]
    queue_area = sum(area(r['a'], r['s'], start, end) for r in relevant)
    busy_area = sum(area(r['s'], r['e'], start, end) for r in relevant)
    events = {}
    for r in relevant:
        if r['s'] > r['a'] and r['s'] > start:
            left, right = max(start, r['a']), min(end, r['s'])
            if left < right:
                events[left] = events.get(left, 0) + 1
                events[right] = events.get(right, 0) - 1
    count = maximum = 0
    for t, delta in sorted(events.items()):
        count += delta
        maximum = max(maximum, count)
    bins = []
    for i in range(math.ceil(duration / 10)):
        left = i * 10
        minutes = min(10, duration - left)
        n = sum(left <= (r['a'] - start).total_seconds() / 60 < left + minutes for r in cohort)
        bins.append({'minute': left, 'count': n, 'rate_hour': n * 60 / minutes})
    mean_service = statistics.mean(service)
    warnings = ['Hipótese para cenários: fila única FIFO, todos os clientes podem usar qualquer tipo de posto e capacidade constante. Não representa filas separadas ou auxílio compartilhado nos totens.']
    if any(r['a'] < start for r in relevant):
        warnings.append('Há clientes anteriores à janela: entram nas áreas de fila/ocupação, mas não na média de espera da coorte de chegadas.')
    if any(r['e'] > end for r in cohort):
        warnings.append('Clientes que chegaram na janela foram acompanhados até o fim: suas esperas completas incluem o período posterior.')
    if len(cohort) < 30:
        warnings.append('Poucas chegadas: use como piloto. A suficiência da amostra depende da variabilidade e do objetivo da análise.')
    if any((r['origem'] or '').upper() not in ('FICTICIO', 'REAL', 'SINTETICO') for r in rows):
        warnings.append('Há registros sem origem REAL, SINTETICO ou FICTICIO. Confirme a procedência antes de usar no relatório.')
    return {
        'count': len(cohort), 'records': len(rows), 'duration_min': duration,
        'completed': sum(start <= r['e'] < end for r in relevant),
        'arrival_hour': len(cohort) / duration * 60,
        'service_min': mean_service, 'service_hour': 60 / mean_service,
        'wait_min': statistics.mean(waits), 'system_min': statistics.mean(system),
        'queue_mean': queue_area / duration,
        'system_mean': sum(area(r['a'], r['e'], start, end) for r in relevant) / duration,
        'utilization': busy_area / (cashiers * duration), 'queue_max': maximum,
        'initial_system': sum(r['a'] < start < r['e'] for r in relevant),
        'remaining': sum(r['a'] < end < r['e'] for r in relevant),
        'bins': bins, 'warnings': warnings,
        'source': 'FICTICIO' if any(r['origem'].upper() == 'FICTICIO' for r in rows) else 'SINTETICO' if any(r['origem'].upper() == 'SINTETICO' for r in rows) else 'REAL' if all(r['origem'].upper() == 'REAL' for r in rows) else 'NAO_INFORMADA',
    }, service


def mmc(arrival_min, service_min, cashiers):
    rho = arrival_min * service_min / cashiers
    if rho >= 1:
        return {'stable': False, 'utilization': rho, 'wait_min': None, 'system_min': None, 'queue_mean': None, 'system_mean': None}
    offered = arrival_min * service_min
    # Erlang B recursivo evita fatoriais grandes; conversão para Erlang C.
    erlang_b = 1.0
    for n in range(1, cashiers + 1):
        erlang_b = offered * erlang_b / (n + offered * erlang_b)
    wait_probability = erlang_b / (1 - rho + rho * erlang_b)
    wait = wait_probability / (cashiers / service_min - arrival_min)
    return {'stable': True, 'utilization': rho, 'wait_min': wait,
            'system_min': wait + service_min, 'queue_mean': arrival_min * wait,
            'system_mean': arrival_min * (wait + service_min)}


def distribute(jobs, normal, automatic, horizon):
    """FIFO dentro do tipo escolhido; conserva chegadas e durações, redistribui postos."""
    initial = min([0] + [j['arrival'] for j in jobs])
    heaps = {'normal': [(initial, i) for i in range(normal)],
             'self': [(initial, normal+i) for i in range(automatic)]}
    for heap in heaps.values():
        heapq.heapify(heap)
    timeline = []
    for job in sorted(jobs, key=lambda j: j['arrival']):
        heap = heaps[job['kind']]
        if not heap:
            raise ValueError('Há demanda para um tipo sem postos. Mantenha ao menos um posto desse tipo; não presumimos troca de modalidade.')
        free, station = heapq.heappop(heap)
        begin = max(job['arrival'], free)
        finish = begin + job['duration']
        heapq.heappush(heap, (finish, station))
        timeline.append({'id': job['id'], 'arrival': job['arrival'], 'start': begin, 'end': finish, 'station': station})
    cohort = [j for j in timeline if 0 <= j['arrival'] < horizon]
    return {'timeline': timeline, 'wait_min': statistics.mean(j['start']-j['arrival'] for j in cohort) if cohort else None,
            'system_min': statistics.mean(j['end']-j['arrival'] for j in cohort) if cohort else None,
            'queue_mean': sum(max(0, min(j['start'], horizon)-max(j['arrival'], 0)) for j in timeline)/horizon,
            'utilization': sum(max(0, min(j['end'], horizon)-max(j['start'], 0)) for j in timeline)/((normal+automatic)*horizon),
            'completed': sum(0 <= j['end'] < horizon for j in timeline), 'arrivals': len(cohort)}


def simulate_types(rate, pools, normal, automatic, horizon, factor, seed, normal_share):
    runs = []
    timeline = []
    for repetition in range(30):
        arrivals_rng = random.Random(seed+repetition*3)
        type_rng = random.Random(seed+repetition*3+1)
        service_rng = random.Random(seed+repetition*3+2)
        jobs = []
        arrival = arrivals_rng.expovariate(rate)
        while arrival < horizon:
            if len(jobs) >= 20000:
                raise ValueError('Limite de chegadas excedido.')
            kind = 'normal' if type_rng.random() < normal_share else 'self'
            jobs.append({'id': f'S{len(jobs)+1:04}', 'arrival': arrival, 'duration': service_rng.choice(pools[kind])*factor, 'kind': kind})
            arrival += arrivals_rng.expovariate(rate)
        run = distribute(jobs, normal, automatic, horizon)
        trace = run.pop('timeline')
        if repetition == 0:
            timeline = trace
        runs.append(run)
    result = {key: statistics.mean(r[key] for r in runs if r[key] is not None) if any(r[key] is not None for r in runs) else None for key in runs[0]}
    waits = [r['wait_min'] for r in runs if r['wait_min'] is not None]
    result.update(timeline=timeline, repetitions=30, wait_sd_min=statistics.stdev(waits) if len(waits)>1 else None)
    return result


def run_queue(jobs, cashiers, horizon, trace=False):
    """FIFO sem abandono; áreas limitadas à janela, tempos da coorte completos."""
    available = [(0.0, i) for i in range(cashiers)]
    heapq.heapify(available)
    waits, systems = [], []
    queue_area = busy_area = 0.0
    completed = 0
    timeline = []
    for arrival, service in jobs:
        free, station = heapq.heappop(available)
        begin = max(arrival, free)
        if isinstance(service, list):
            service = service[station]
        finish = begin + service
        heapq.heappush(available, (finish, station))
        if trace:
            timeline.append({'id': f'S{len(timeline) + 1:04}', 'arrival': arrival, 'start': begin, 'end': finish, 'station': station})
        waits.append(begin - arrival)
        systems.append(finish - arrival)
        queue_area += max(0, min(begin, horizon) - arrival)
        busy_area += max(0, min(finish, horizon) - min(begin, horizon))
        completed += finish < horizon
    result = {'wait_min': statistics.mean(waits) if waits else None,
            'system_min': statistics.mean(systems) if systems else None,
            'queue_mean': queue_area / horizon, 'utilization': busy_area / (cashiers * horizon),
            'completed': completed, 'arrivals': len(waits)}
    if trace:
        result['timeline'] = timeline
    return result


def simulate(rate, services, cashiers, horizon, factor, seed, repetitions=30, station_services=None):
    results = []
    timeline = []
    for repetition in range(repetitions):
        arrivals_rng = random.Random(seed + repetition * 2)
        service_rng = random.Random(seed + repetition * 2 + 1)
        arrival = arrivals_rng.expovariate(rate)
        jobs = []
        while arrival < horizon:
            if len(jobs) >= 20000:
                raise ValueError('Cenário excede 20.000 chegadas por repetição. Reduza a janela ou a demanda.')
            if station_services:
                u = service_rng.random()
                service = [pool[min(int(u * len(pool)), len(pool)-1)] * factor for pool in station_services]
            else:
                service = service_rng.choice(services) * factor
            jobs.append((arrival, service))
            arrival += arrivals_rng.expovariate(rate)
        run = run_queue(jobs, cashiers, horizon, trace=repetition == 0)
        if repetition == 0:
            timeline = run.pop('timeline')
        results.append(run)
    result = {'repetitions': repetitions}
    for key in results[0]:
        values = [r[key] for r in results if r[key] is not None]
        result[key] = statistics.mean(values) if values else None
    waits = [r['wait_min'] for r in results if r['wait_min'] is not None]
    result['wait_sd_min'] = statistics.stdev(waits) if len(waits) > 1 else None
    result['nonempty_repetitions'] = len(waits)
    result['timeline'] = timeline
    return result


def analyze(payload):
    if not isinstance(payload, dict):
        raise ValueError('Requisição inválida.')
    rows = parse_csv(payload.get('csv'))
    start, end = timestamp(payload.get('start')), timestamp(payload.get('end'))
    cashiers = number(payload.get('cashiers'), 'Caixas', 1, 20, True)
    normal = number(payload.get('normal_cashiers', cashiers), 'Caixas convencionais', 0, 20, True)
    automatic = number(payload.get('self_cashiers', 0), 'Totens', 0, 20, True)
    if normal + automatic != cashiers:
        raise ValueError('Total de postos deve ser igual a convencionais + totens (1 a 20).')
    mapping = payload.get('station_types', {r['caixa']: {'C':'normal','CA':'self'}.get(r['caixa'], r['tipo_caixa'] or 'normal') for r in rows})
    if not isinstance(mapping, dict) or set(mapping) != {r['caixa'] for r in rows} or any(v not in ('normal', 'self') for v in mapping.values()):
        raise ValueError('Classifique cada posto do CSV como normal ou self.')
    seed = number(payload.get('seed', 7002), 'Semente', 0, 1000000, True)
    obs, services = observed(rows, start, end, cashiers)
    obs['warnings'][0] = 'Distribuição FIFO dentro do tipo C/CA escolhido na coleta. A quantidade de postos altera a projeção; a espera observada permanece fixa. Não simulamos migração entre tipos ou auxílio compartilhado.'
    obs['utilization'] = None  # IDs de tipo não informam capacidade histórica; não usar capacidade de cenário no observado.
    cohort = [r for r in rows if start <= r['a'] < end]
    normal_share = sum(mapping[r['caixa']] == 'normal' for r in cohort)/len(cohort)
    pools = {kind: [(r['e']-r['s']).total_seconds()/60 for r in rows if mapping[r['caixa']] == kind and r['a'] < end and r['e'] > start] for kind in ('normal','self')}
    ratio = payload.get('self_service_ratio')
    if ratio is not None:
        ratio = number(ratio, 'Duração do totem (% do convencional)', 10, 500) / 100
    assumed = []
    for kind, other in (('normal','self'),('self','normal')):
        if not pools[kind] and pools[other]:
            # Só exigimos a hipótese se algum cenário efetivamente usar o tipo sem amostra.
            if ratio is not None:
                pools[kind] = [v * ratio if kind == 'self' else v / ratio for v in pools[other]]
                assumed.append(kind)
    scenarios = payload.get('scenarios', [])
    if not isinstance(scenarios, list) or len(scenarios) > 7:
        raise ValueError('Use até 7 cenários alternativos.')
    cases = [{'name': 'Configuração atual', 'demand_pct': 0, 'service_pct': 0, 'cashiers': cashiers, 'normal_cashiers': normal, 'self_cashiers': automatic}] + scenarios
    prepared = []
    for case in cases:
        if not isinstance(case, dict) or not isinstance(case.get('name'), str) or not 1 <= len(case['name'].strip()) <= 60:
            raise ValueError('Cada cenário precisa de nome entre 1 e 60 caracteres.')
        demand = number(case.get('demand_pct'), 'Variação de demanda (%)', -80, 200)
        speed = number(case.get('service_pct'), 'Variação da duração (%)', -80, 200)
        c = number(case.get('cashiers'), 'Caixas no cenário', 1, 20, True)
        nc = number(case.get('normal_cashiers', c), 'Convencionais no cenário', 0, 20, True)
        ac = number(case.get('self_cashiers', 0), 'Totens no cenário', 0, 20, True)
        if nc + ac != c:
            raise ValueError('A soma dos tipos de posto no cenário deve coincidir com o total.')
        if (nc and not pools['normal']) or (ac and not pools['self']):
            raise ValueError('Faltam tempos observados para um tipo de posto. Informe uma hipótese de duração relativa para o tipo sem amostra na configuração.')
        rate = obs['arrival_hour'] / 60 * (1 + demand / 100)
        if rate * obs['duration_min'] > 10000:
            raise ValueError('Cenário com mais de 10.000 chegadas esperadas. Reduza a janela ou a demanda.')
        prepared.append((case, demand, speed, c, rate, nc, ac))
    output = []
    for case, demand, speed, c, rate, nc, ac in prepared:
        factor = 1 + speed / 100
        station_pools = [pools['normal']] * nc + [pools['self']] * ac
        mean_service = statistics.mean(statistics.mean(pool) for pool in station_pools) * factor
        theory = mmc(rate, mean_service, c) if not (nc and ac) else {'stable': None, 'wait_min': None, 'reason': 'Tipos diferentes: use a simulação; M/M/c exige postos equivalentes.'}
        if (normal_share > 0 and not nc) or (normal_share < 1 and not ac):
            raise ValueError('Mantenha pelo menos um posto para cada tipo de atendimento presente na coleta.')
        jobs = [{'id': r['id'], 'arrival': (r['a']-start).total_seconds()/60,
                 'duration': (r['e']-r['s']).total_seconds()/60*factor, 'kind': mapping[r['caixa']]}
                for r in rows if r['a'] < end]
        # A projeção conserva a coorte: variações de demanda são avaliadas nas repetições Poisson.
        projection = distribute(jobs, nc, ac, obs['duration_min'])
        output.append({'name': case['name'].strip(), 'demand_pct': demand, 'service_pct': speed, 'cashiers': c,
                       'normal_cashiers': nc, 'self_cashiers': ac,
                       'arrival_hour': rate * 60, 'service_min': mean_service,
                       'theory': theory, 'projection': projection,
                       'simulation': simulate_types(rate, pools, nc, ac, obs['duration_min'], factor, seed, normal_share)})
    used_assumption = any((nc and 'normal' in assumed) or (ac and 'self' in assumed) for _,_,_,_,_,nc,ac in prepared)
    if used_assumption and ratio is not None:
        obs['warnings'].append(f'Hipótese informada: duração do autoatendimento = {ratio*100:g}% da duração convencional, usada onde não há amostra desse tipo.')
    return {'observed': obs, 'scenarios': output, 'seed': seed,
            'configuration': {'normal_cashiers': normal, 'self_cashiers': automatic, 'station_types': mapping, 'self_service_ratio': None if ratio is None else ratio*100},
            'rows': [{key: row[key] for key in FIELDS} for row in rows]}
