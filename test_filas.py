import unittest
from datetime import datetime
from pathlib import Path

from filas import analyze, inspect_data, mmc, observed, parse_csv, run_queue


class QueueTests(unittest.TestCase):
    def test_type_csv_redistributes_to_added_stations(self):
        text = (Path(__file__).parent/'dados/Angeloni_pico_por_tipo.csv').read_text(encoding='utf-8-sig')
        info = inspect_data({'csv': text})
        payload = {'csv':text, 'start':info['observation_start'], 'end':info['observation_end'], 'cashiers':10, 'normal_cashiers':4, 'self_cashiers':6}
        base = analyze(payload)
        self.assertAlmostEqual(base['scenarios'][0]['projection']['wait_min'], base['observed']['wait_min'])
        for normal, automatic in [(6,6),(4,8),(6,8)]:
            changed = analyze(dict(payload, cashiers=normal+automatic, normal_cashiers=normal, self_cashiers=automatic))
            projected = changed['scenarios'][0]['projection']
            self.assertLess(projected['wait_min'], base['scenarios'][0]['projection']['wait_min'])
            self.assertEqual(changed['observed']['wait_min'], base['observed']['wait_min'])
            self.assertEqual(len({j['station'] for j in projected['timeline']}), normal+automatic)
            for j in projected['timeline']:
                row = next(r for r in changed['rows'] if r['id']==j['id'])
                self.assertEqual(j['station'] < normal, row['caixa']=='C')

    def test_peak_load_fixture(self):
        text = (Path(__file__).parent / 'dados/Angeloni_pico.csv').read_text(encoding='utf-8-sig')
        info = inspect_data({'csv': text})
        self.assertEqual(info['records'], 968)
        self.assertEqual(list(info['station_types'].values()).count('normal'), 4)
        self.assertEqual(list(info['station_types'].values()).count('self'), 6)
        result = analyze({'csv': text, 'start': info['observation_start'], 'end': info['observation_end'],
                          'cashiers': 10, 'normal_cashiers': 4, 'self_cashiers': 6, 'station_types': info['station_types']})
        self.assertEqual(result['observed']['source'], 'SINTETICO')
        self.assertGreater(result['observed']['queue_max'], 50)
        self.assertEqual(result['observed']['duration_min'], 180)
        self.assertTrue(all(row['tipo_caixa'] == info['station_types'][row['caixa']] for row in result['rows']))

    def demo_payload(self):
        return {'csv': (Path(__file__).parent / 'dados/Angelone_pico_FICTICIO.csv').read_text(encoding='utf-8-sig'),
                'start': '2026-11-03 17:30:00', 'end': '2026-11-03 19:00:00', 'cashiers': 2}

    def test_inspection_has_no_invented_capacity_or_window(self):
        result = inspect_data(self.demo_payload())
        self.assertEqual(result['stations'], ['C1', 'C2'])
        self.assertEqual(result['records'], 78)
        self.assertEqual(result['names'], ['Angelone'])
        with self.assertRaises(ValueError):
            inspect_data({'csv': 'bad file'})

    def test_mixed_stations_and_type_capacity(self):
        payload = self.demo_payload()
        payload.update(normal_cashiers=1, self_cashiers=1, station_types={'C1': 'normal', 'C2': 'self'})
        result = analyze(payload)
        self.assertIsNone(result['scenarios'][0]['theory']['stable'])
        self.assertEqual(result['configuration']['station_types'], payload['station_types'])
        payload['station_types']['C2'] = 'normal'
        with self.assertRaises(ValueError):
            analyze(payload)

    def test_missing_type_requires_explicit_hypothesis(self):
        payload = self.demo_payload()
        payload.update(cashiers=3, normal_cashiers=2, self_cashiers=1, station_types={'C1': 'normal', 'C2': 'normal'})
        with self.assertRaises(ValueError):
            analyze(payload)
        payload['self_service_ratio'] = 120
        result = analyze(payload)
        self.assertTrue(any('120%' in text for text in result['observed']['warnings']))
        self.assertEqual(result['scenarios'][0]['self_cashiers'], 1)

    def test_heterogeneous_trace_uses_assigned_station_duration(self):
        result = run_queue([(0, [4, 1]), (0, [4, 1]), (1, [4, 1])], 2, 10, trace=True)
        self.assertEqual([j['station'] for j in result['timeline']], [0, 1, 1])
        self.assertEqual([j['end']-j['start'] for j in result['timeline']], [4, 1, 1])

    def test_known_mm1(self):
        result = mmc(12 / 60, 4, 1)
        self.assertAlmostEqual(result['wait_min'], 16)
        self.assertAlmostEqual(result['system_min'], 20)
        self.assertAlmostEqual(result['queue_mean'], 3.2)
        self.assertFalse(mmc(0.5, 4, 2)['stable'])

    def test_trace_matches_service_and_capacity(self):
        result = run_queue([(0, 4), (1, 2), (2, 3), (3, 1)], 2, 10, trace=True)
        events = result['timeline']
        self.assertEqual(len(events), 4)
        self.assertAlmostEqual(result['wait_min'], sum(e['start']-e['arrival'] for e in events)/4)
        self.assertEqual([e['end']-e['start'] for e in events], [4, 2, 3, 1])
        for station in range(2):
            visits = [e for e in events if e['station'] == station]
            self.assertTrue(all(b['start'] >= a['end'] for a,b in zip(visits,visits[1:])))

    def test_known_mm2(self):
        result = mmc(1, 1, 2)
        self.assertAlmostEqual(result['wait_min'], 1 / 3)
        self.assertAlmostEqual(result['utilization'], 0.5)

    def test_deterministic_simulation_and_window(self):
        result = run_queue([(0, 4), (1, 3), (3, 5)], 1, 6)
        self.assertAlmostEqual(result['wait_min'], 7 / 3)
        self.assertAlmostEqual(result['queue_mean'], 1)
        self.assertAlmostEqual(result['utilization'], 1)
        self.assertEqual(result['completed'], 1)

    def test_bad_csv_and_overlap(self):
        header = 'id,chegada,inicio_atendimento,fim_atendimento,caixa,fila\n'
        row = '1,2026-11-03 18:00:00,2026-11-03 18:01:00,2026-11-03 18:04:00,C1,F1\n'
        with self.assertRaises(ValueError):
            parse_csv(header + row + row)
        with self.assertRaises(ValueError):
            parse_csv(header + row + row.replace('1,2026', '2,2026', 1))
        with self.assertRaises(ValueError):
            parse_csv(header + row.replace('18:04:00', '17:00:00'))

    def test_observation_boundaries(self):
        csv = 'id,chegada,inicio_atendimento,fim_atendimento,caixa,fila\n'
        csv += '1,2026-11-03 17:59:00,2026-11-03 18:01:00,2026-11-03 18:04:00,C1,F1\n'
        csv += '2,2026-11-03 18:02:00,2026-11-03 18:04:00,2026-11-03 18:08:00,C1,F1\n'
        result, _ = observed(parse_csv(csv), datetime(2026, 11, 3, 18), datetime(2026, 11, 3, 18, 6), 1)
        self.assertEqual(result['count'], 1)
        self.assertAlmostEqual(result['wait_min'], 2)
        self.assertAlmostEqual(result['queue_mean'], 0.5)
        self.assertAlmostEqual(result['utilization'], 5 / 6)
        self.assertEqual(result['initial_system'], 1)
        self.assertEqual(result['remaining'], 1)

    def test_demo_reproducibility_and_more_capacity(self):
        text = (Path(__file__).parent / 'dados/Angelone_pico_FICTICIO.csv').read_text(encoding='utf-8-sig')
        payload = {'csv': text, 'start': '2026-11-03 17:30:00', 'end': '2026-11-03 19:00:00', 'cashiers': 2,
                   'scenarios': [{'name': 'Mais um caixa', 'cashiers': 3, 'demand_pct': 0, 'service_pct': 0}]}
        first, second = analyze(payload), analyze(payload)
        self.assertEqual(first, second)
        self.assertEqual(first['observed']['source'], 'FICTICIO')
        self.assertLessEqual(first['scenarios'][1]['simulation']['wait_min'], first['scenarios'][0]['simulation']['wait_min'])
        payload['cashiers'] = 1.5
        with self.assertRaises(ValueError):
            analyze(payload)


if __name__ == '__main__':
    unittest.main()
