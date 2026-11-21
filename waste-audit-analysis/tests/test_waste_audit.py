"""Tests for waste_audit.py. Run: python -m unittest discover -s tests"""
import json, os, subprocess, sys, tempfile, unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, 'scripts'))
import waste_audit as wa  # noqa: E402

EX = os.path.join(ROOT, 'examples')


def run_cfg(cfg, base):
    wa.ISSUES.clear()
    for a in cfg['areas']:
        a['file'] = os.path.join(base, a['file']) if not os.path.isabs(a['file']) else a['file']
    out = tempfile.mkdtemp()
    return wa.analyse(cfg, out), out


class Synthetic(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        subprocess.run([sys.executable, os.path.join(EX, 'make_synthetic.py')], check=True, capture_output=True)
        cls.answer = json.load(open(os.path.join(EX, 'synthetic', 'ANSWER.json')))
        cls.cfg = json.load(open(os.path.join(EX, 'synthetic-config.json')))
        cls.t, cls.out = run_cfg(cls.cfg, EX)
        cls.issues = cls.t['data_issues']

    def gen(self, area):
        g = self.t['generation']
        return g[(g['area'] == area) & (g['source'] == 'household')].iloc[0]

    def test_clean_area_matches_truth(self):
        # hillside has no planted weight errors: the script must recover the known answer from grams
        self.assertAlmostEqual(self.gen('hillside')['kg_cap_day_ratio_of_totals'],
                               self.answer['truth_clean_data']['hillside']['kg_cap_day'], places=3)

    def test_planted_problems_flagged(self):
        r = self.issues[self.issues['area'] == 'riverside']
        kinds = set(r['kind'])
        for k in ['non-numeric weight', 'household size not whole', 'outliers', 'duplicate rows', 'all-zero category',
                  'BELOW BENCHMARK', 'no municipal total', 'density', 'period']:
            self.assertIn(k, kinds)
        self.assertIn('R071', ' '.join(r[r['kind'] == 'outliers']['detail']))
        self.assertIn('income missing', set(self.issues[self.issues['area'] == 'hillside']['kind']))

    def test_both_averages_reported(self):
        g = self.gen('riverside')
        self.assertIn('kg_cap_day_mean_of_ratios', g.index)
        self.assertIn('kg_cap_day_ratio_of_totals', g.index)

    def test_daily_sensitivity_is_period_times(self):
        s = self.t['sensitivity']
        base = s[(s['area'] == 'hillside') & (s['case'] == 'base')]['kg_cap_day'].iloc[0]
        daily = s[(s['area'] == 'hillside') & (s['case'] == 'if weights were daily')]['kg_cap_day'].iloc[0]
        self.assertAlmostEqual(daily / base, 7, places=6)

    def test_low_rate_flagged_without_benchmark(self):
        # the cold test's main gap: with no benchmark, a 0.10 kg/cap/day rate went unflagged
        self.assertIn('RATE OUTSIDE PLAUSIBLE RANGE', set(self.issues['kind']))

    def test_effects_measured(self):
        r = self.issues[self.issues['area'] == 'riverside'].set_index('kind')['effect']
        for k in ['duplicate rows', 'non-numeric weight', 'outliers', 'household size not whole']:
            self.assertIn('kg/cap/day', r[k])

    def test_flows_recyclables(self):
        fl = self.t['flows_household_t_day']
        h = fl[fl['area'] == 'hillside']
        g = self.gen('hillside')
        self.assertAlmostEqual(h['t_day_measured'].sum(), g['household_t_day_unadjusted'], places=6)

    def test_summary_written(self):
        self.assertTrue(os.path.exists(os.path.join(self.out, 'summary.md')))


class Rules(unittest.TestCase):
    def _area(self, text, **kw):
        d = tempfile.mkdtemp()
        p = os.path.join(d, 'a.csv')
        open(p, 'w', encoding='utf-8').write(text)
        cfg = {'areas': [dict({'name': 'A', 'file': p, 'unit': 'kg', 'period_days': 1, 'weights_are': 'daily'}, **kw)],
               'id_col': 'id', 'type_col': 'type', 'people_col': 'people', 'categories': {'food': 'organic', 'bag': 'plastic'}}
        return cfg

    def test_hash_in_values_is_not_a_comment(self):
        # the STOP re-run lost every 'Education #1' row to read_csv(comment='#')
        cfg = self._area('# note row\nid,type,people,food,bag\n1,household,2,0.4,0.1\n2,School #1,,1.0,0.5\n')
        t, _ = run_cfg(cfg, '')
        self.assertIn('School #1', set(t['generation']['source']))

    def test_grams_converted(self):
        cfg = self._area('id,type,people,food,bag\n1,household,2,400,100\n', unit='g')
        t, _ = run_cfg(cfg, '')
        g = t['generation']
        self.assertAlmostEqual(g[g['source'] == 'household']['kg_hh_day'].iloc[0], 0.5)

    def test_adjustment_needs_reason_and_source(self):
        cfg = self._area('id,type,people,food,bag\n1,household,2,0.4,0.1\n')
        cfg['adjustments'] = [{'area': 'A', 'category': 'organic', 'add_kg_cap_day': 0.1}]
        with self.assertRaises(SystemExit):
            run_cfg(cfg, '')

    def test_adjustment_shown_not_silent(self):
        cfg = self._area('id,type,people,food,bag\n1,household,2,0.4,0.1\n')
        cfg['adjustments'] = [{'area': 'A', 'category': 'organic', 'add_kg_cap_day': 0.1, 'reason': 'missed food waste', 'source': 'test'}]
        t, out = run_cfg(cfg, '')
        g = t['generation'].iloc[0]
        self.assertAlmostEqual(g['kg_cap_day_ratio_of_totals'], 0.25)
        self.assertAlmostEqual(g['kg_cap_day_adjusted'], 0.35)
        self.assertIn('missed food waste', open(os.path.join(out, 'summary.md'), encoding='utf-8').read())

    def test_unit_suspect_flagged(self):
        # grams declared as kg: a 400 'kg' household per day must trip the unit check
        cfg = self._area('id,type,people,food,bag\n1,household,2,400,100\n2,household,3,300,90\n')
        t, _ = run_cfg(cfg, '')
        self.assertIn('UNIT OR PERIOD SUSPECT', set(t['data_issues']['kind']))


if __name__ == '__main__':
    unittest.main()
