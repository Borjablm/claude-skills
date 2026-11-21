#!/usr/bin/env python3
"""Waste audit analysis: from tally sheets to generation rates and composition.

Input: one tidy CSV per area (one row per sampled household or non-household unit)
and a JSON config. Output: tables (CSV) and a markdown summary with a data-quality
log and an assumptions register. Every number in the summary comes from the tables.

Usage:
    python waste_audit.py config.json --out results/
    python waste_audit.py config.json --checks-only    # pre-flight checks, no results

Config keys (see templates/config.example.json):
    areas: list of {name, file, unit ("kg" or "g"), period_days, weights_are ("period_total" or "daily"),
                    population (optional), households (optional)}
    id_col, type_col, people_col, income_col (optional)
    household_type: value of type_col that marks households (default "household")
    categories: {column_name: material_group}
    income_bands: list of [label, lower_inclusive, upper_exclusive] or omitted
    benchmark_kg_cap_day: [low, high] reference range for households (optional)
    adjustments: list of {area, category, add_kg_cap_day, reason, source}  (optional; shown, never silent)
    nonhousehold_counts: {area: {source_type: count}}  (optional; needed for a municipal total)
    density: {area: {volume_litres: float, weight_kg: float}} or omitted
"""
import argparse, json, math, os, random, sys

import pandas as pd

ISSUES = []
DEFAULT_RECYCLABLE = ['plastic', 'paper', 'glass', 'metal']


def issue(area, kind, detail, effect='not quantified'):
    ISSUES.append({'area': area, 'kind': kind, 'detail': detail, 'effect': effect})


def set_effect(area, kind, delta, how):
    for i in ISSUES:
        if i['area'] == area and i['kind'] == kind:
            i['effect'] = f'{delta:+.4f} kg/cap/day {how}'


def load_area(cfg, a):
    # Leading note rows start with '#'. Skip only those: never use comment='#', which also cuts
    # any value containing '#' (a real failure in the STOP re-run).
    with open(a['file'], encoding='utf-8') as f:
        lines = f.read().splitlines()
    skip = next(i for i, l in enumerate(lines) if not l.lstrip('"').startswith('#'))
    a['notes'] = [l.strip('"') for l in lines[:skip]]
    df = pd.read_csv(a['file'], skiprows=skip)
    cats = list(cfg['categories'])
    missing = [c for c in cats if c not in df.columns]
    if missing:
        sys.exit(f"{a['name']}: category columns missing: {missing}")
    alt = df[cats].copy()  # a second reading with decimal commas parsed, used only to size the effect
    for c in cats:
        bad = pd.to_numeric(df[c], errors='coerce').isna() & df[c].notna()
        if bad.any():
            rid = df.loc[bad, cfg['id_col']].tolist() if cfg.get('id_col') else df.index[bad].tolist()
            issue(a['name'], 'non-numeric weight', f"{c}: {list(zip(rid, df.loc[bad, c].tolist()))[:10]} set to empty "
                  "(excluded from sums); fix at source")
        alt[c] = pd.to_numeric(df[c].astype(str).str.replace(',', '.', regex=False), errors='coerce').where(df[c].notna())
        df[c] = pd.to_numeric(df[c], errors='coerce')
    a['_alt_weights'] = alt
    return df


def preflight(cfg, a, df):
    """Checks that decide whether the numbers mean anything. They raise issues; they never fix silently."""
    cats = list(cfg['categories'])
    tcol, hh = cfg.get('type_col'), cfg.get('household_type', 'household')
    is_hh = df[tcol].eq(hh) if tcol else pd.Series(True, index=df.index)
    tot = df.loc[is_hh, cats].sum(axis=1)
    med = float(tot.median()) if len(tot) else float('nan')
    # 1. unit sanity: a household sample is rarely below 0.05 kg or above 30 kg per day
    per_day_kg = med / (1000 if a['unit'] == 'g' else 1) / (a['period_days'] if a['weights_are'] == 'period_total' else 1)
    if not (0.05 <= per_day_kg <= 30):
        issue(a['name'], 'UNIT OR PERIOD SUSPECT',
              f"median household = {per_day_kg:.3f} kg/day with unit={a['unit']}, period_days={a['period_days']}, "
              f"weights_are={a['weights_are']}. Check the header unit and whether weights are totals or daily.")
    # 2. day divisor
    if a['weights_are'] == 'period_total' and a['period_days'] < 8:
        issue(a['name'], 'period', f"{a['period_days']} days analysed. Studies following SNI 19-3964-1994 sample 8 consecutive days; "
              "studies often drop day 1. Confirm which days are in the totals.")
    # 3. people per household
    if cfg.get('people_col'):
        p = pd.to_numeric(df.loc[is_hh, cfg['people_col']], errors='coerce')
        if p.isna().any():
            issue(a['name'], 'household size missing', f"{int(p.isna().sum())} households; excluded from per-capita")
        frac = p.dropna() % 1
        if (frac > 0).any():
            fx = frac[frac > 0].index
            ids = df.loc[fx, cfg['id_col']].tolist() if cfg.get('id_col') else list(fx)
            issue(a['name'], 'household size not whole', f"{len(fx)} values like {p[fx[0]]} in {ids[:10]}; "
                  "often a mean typed in for a missing value")
    # 4. all-zero categories and empty rows
    zero = [c for c in cats if df.loc[is_hh, c].fillna(0).eq(0).all()]
    if zero:
        issue(a['name'], 'all-zero category', f"{zero} are zero in every household; real absence or not sorted?")
    empty = int((tot.fillna(0) == 0).sum())
    if empty:
        issue(a['name'], 'empty sample', f"{empty} households with zero total weight")
    # 5. outliers: per person when household size is known (a big household is not an outlier), Q3 + 3 IQR
    basis = tot
    if cfg.get('people_col'):
        p = pd.to_numeric(df.loc[is_hh, cfg['people_col']], errors='coerce')
        basis = (tot / p).where(p > 0)
    q1, q3 = basis.quantile(.25), basis.quantile(.75)
    out = basis > q3 + 3 * (q3 - q1)
    if out.any():
        ids = df.loc[out[out].index, cfg['id_col']].tolist() if cfg.get('id_col') else out[out].index.tolist()
        issue(a['name'], 'outliers', f"{int(out.sum())} households above Q3+3IQR per person: {ids[:10]} (kept; see sensitivity)")
    # 6. duplicates
    dup = df.duplicated(subset=cats, keep=False) & (df[cats].fillna(0).sum(axis=1) > 0)
    if dup.any():
        ids = df.loc[dup, cfg['id_col']].tolist() if cfg.get('id_col') else df.index[dup].tolist()
        issue(a['name'], 'duplicate rows', f"{int(dup.sum())} rows with identical weights {ids[:10]}; data-entry copy? (kept)")
    a['_dup_later'] = df.duplicated(subset=cats, keep='first') & (df[cats].fillna(0).sum(axis=1) > 0)
    # 7. income values that are not numbers (flagged whether or not bands are configured)
    if cfg.get('income_col'):
        iv = df.loc[is_hh, cfg['income_col']]
        badi = pd.to_numeric(iv, errors='coerce').isna()
        if badi.any():
            issue(a['name'], 'income missing', f"{int(badi.sum())} households without a usable income "
                  f"(values: {sorted(set(map(str, iv[badi].tolist())))[:5]})")
    return is_hh, out


def to_kg_day(a, s):
    s = s / (1000 if a['unit'] == 'g' else 1)
    return s / a['period_days'] if a['weights_are'] == 'period_total' else s


def boot_ratio(kg, ppl, n=2000, seed=1):
    rng = random.Random(seed)
    idx = list(range(len(kg)))
    vals = []
    for _ in range(n):
        b = [rng.choice(idx) for _ in idx]
        vals.append(sum(kg[i] for i in b) / sum(ppl[i] for i in b))
    vals.sort()
    return vals[int(.025 * n)], vals[int(.975 * n)]


def analyse(cfg, out_dir):
    os.makedirs(out_dir, exist_ok=True)
    cats, groups = list(cfg['categories']), cfg['categories']
    hh_rows, gen, comp, inc, sens, flows = [], [], [], [], [], []
    for x in cfg.get('adjustments', []):
        if not (x.get('reason') and x.get('source')):
            sys.exit(f'adjustment without reason and source: {x}. Every adjustment must say why and on what basis.')
    for a in cfg['areas']:
        df = load_area(cfg, a)
        is_hh, outl = preflight(cfg, a, df)
        kg = to_kg_day(a, df[cats])
        h = kg[is_hh].copy()
        ppl = pd.to_numeric(df.loc[is_hh, cfg['people_col']], errors='coerce') if cfg.get('people_col') else None
        ok = ppl.notna() if ppl is not None else pd.Series(True, index=h.index)
        tot = h.sum(axis=1)
        row = {'area': a['name'], 'households': int(is_hh.sum()), 'kg_hh_day': tot.mean()}
        if ppl is not None:
            row['kg_cap_day_ratio_of_totals'] = tot[ok].sum() / ppl[ok].sum()
            row['kg_cap_day_mean_of_ratios'] = (tot[ok] / ppl[ok]).mean()
            lo, hi = boot_ratio(tot[ok].tolist(), ppl[ok].tolist())
            row['ci95_low'], row['ci95_high'] = lo, hi
            row['mean_people'] = ppl[ok].mean()
            r0 = row['kg_cap_day_ratio_of_totals']
            # plausibility, independent of any benchmark
            if r0 < 0.2 or r0 > 3:
                issue(a['name'], 'RATE OUTSIDE PLAUSIBLE RANGE',
                      f"{r0:.3f} kg/cap/day is outside a broad 0.2-3 plausibility range (not a benchmark). First check the "
                      "documents: if the header or method note states the unit and period, keep that reading and treat the "
                      "rate as a finding (likely under-capture, or a partial sample). Never change the unit or period reading "
                      "to make a number look plausible.")
            # measured effects of the flagged problems on the per-capita rate
            def rate(kgf, mask):
                t = kgf[is_hh].sum(axis=1)
                m = ok & mask.reindex(t.index, fill_value=True)
                return t[m].sum() / ppl[m].sum()
            dl = a['_dup_later']
            if dl[is_hh].any():
                set_effect(a['name'], 'duplicate rows', rate(kg, ~dl) - r0, 'if later copies are removed')
            if (a['_alt_weights'].fillna(-1) != df[cats].fillna(-1)).any().any():
                set_effect(a['name'], 'non-numeric weight', rate(to_kg_day(a, a['_alt_weights']), pd.Series(True, index=df.index)) - r0,
                           'if decimal commas are read as decimals')
            bm = cfg.get('benchmark_kg_cap_day')
            if bm and row['kg_cap_day_ratio_of_totals'] < bm[0]:
                issue(a['name'], 'BELOW BENCHMARK',
                      f"{row['kg_cap_day_ratio_of_totals']:.3f} kg/cap/day vs reference {bm[0]}-{bm[1]} "
                      f"({cfg.get('benchmark_source', 'SOURCE NOT GIVEN: cite one')}). Possible under-capture "
                      "(food to animals, burning, composting, waste sold before collection). Do not adjust silently.")
            adj = sum(x['add_kg_cap_day'] for x in cfg.get('adjustments', []) if x['area'] == a['name'])
            row['adjustment_kg_cap_day'] = adj
            row['kg_cap_day_adjusted'] = row['kg_cap_day_ratio_of_totals'] + adj
            if a.get('population'):
                row['household_t_day'] = row['kg_cap_day_adjusted'] * a['population'] / 1000
                row['household_t_day_unadjusted'] = row['kg_cap_day_ratio_of_totals'] * a['population'] / 1000
            # sensitivity: without outliers; if weights were daily
            o = outl.reindex(h.index).astype('boolean').fillna(False).astype(bool)
            sens.append({'area': a['name'], 'case': 'base', 'kg_cap_day': row['kg_cap_day_ratio_of_totals']})
            r_out = tot[ok & ~o].sum() / ppl[ok & ~o].sum()
            sens.append({'area': a['name'], 'case': 'outliers removed', 'kg_cap_day': r_out})
            if o.any():
                set_effect(a['name'], 'outliers', r_out - r0, 'if outliers are removed')
            if ppl[ok].mod(1).gt(0).any():
                set_effect(a['name'], 'household size not whole', rate(kg, ~(ppl.mod(1) > 0).reindex(df.index, fill_value=False)) - r0,
                           'if those households are excluded')
            alt = 'daily' if a['weights_are'] == 'period_total' else 'period_total'
            f = a['period_days'] if alt == 'daily' else 1 / a['period_days']
            sens.append({'area': a['name'], 'case': f'if weights were {alt}', 'kg_cap_day': row['kg_cap_day_ratio_of_totals'] * f})
        # non-household
        if cfg.get('type_col'):
            nh = df.loc[~is_hh]
            for t, g in nh.groupby(cfg['type_col']):
                gen.append({'area': a['name'], 'source': t, 'units_sampled': len(g),
                            'kg_unit_day': kg.loc[g.index].sum(axis=1).mean()})
            counts = cfg.get('nonhousehold_counts', {}).get(a['name'])
            if len(nh) and not counts:
                issue(a['name'], 'no municipal total', 'non-household units sampled but no counts of each type in the area; '
                      'a municipal total needs them (business register, school and health facility lists, market stall counts)')
            elif counts and a.get('population'):
                t_nh = sum(c * next((x['kg_unit_day'] for x in gen if x['area'] == a['name'] and x['source'] == s), float('nan'))
                           for s, c in counts.items()) / 1000
                row['nonhousehold_t_day'] = t_nh
                row['municipal_t_day'] = row.get('household_t_day', float('nan')) + t_nh
        d = cfg.get('density', {}).get(a['name'])
        if d:
            row['density_kg_l'] = d['weight_kg'] / d['volume_litres']
        else:
            issue(a['name'], 'density', 'not computable without container volume and matching weights')
        hh_rows.append({**row, 'source': 'household'})
        # composition
        share = h.sum() / h.sum().sum()
        for c in cats:
            comp.append({'area': a['name'], 'source': 'household', 'category': c, 'group': groups[c], 'wt_pct': 100 * share[c]})
        # what a sorting facility would receive from households, measured data (adjustments apply to their own group only)
        if 'household_t_day_unadjusted' in row:
            gshare = share.groupby(pd.Series(groups)).sum()
            adj_by_group = {}
            for x in cfg.get('adjustments', []):
                if x['area'] == a['name']:
                    adj_by_group[x['category']] = adj_by_group.get(x['category'], 0) + x['add_kg_cap_day'] * a['population'] / 1000
            for grp, s in gshare.items():
                flows.append({'area': a['name'], 'group': grp, 'recyclable': grp in cfg.get('recyclable_groups', DEFAULT_RECYCLABLE),
                              't_day_measured': s * row['household_t_day_unadjusted'],
                              't_day_with_adjustments': s * row['household_t_day_unadjusted'] + adj_by_group.get(grp, 0)})
        if cfg.get('type_col') and (~is_hh).any():
            s2 = kg[~is_hh].sum() / kg[~is_hh].sum().sum()
            for c in cats:
                comp.append({'area': a['name'], 'source': 'non-household', 'category': c, 'group': groups[c], 'wt_pct': 100 * s2[c]})
        # income
        if cfg.get('income_col') and ppl is not None:
            if not cfg.get('income_bands'):
                issue(a['name'], 'income bands', 'no band definitions in config; ask for the study\'s own before inventing any')
            else:
                incv = pd.to_numeric(df.loc[is_hh, cfg['income_col']], errors='coerce')
                for lab, lo_, hi_ in cfg['income_bands']:
                    m = ok & incv.ge(lo_) & incv.lt(hi_)
                    inc.append({'area': a['name'], 'band': lab, 'households': int(m.sum()),
                                'kg_cap_day': tot[m].sum() / ppl[m].sum() if m.any() else float('nan')})
                inc.append({'area': a['name'], 'band': 'spearman(income, kg/cap/day)', 'households': int((ok & incv.notna()).sum()),
                            'kg_cap_day': pd.concat([incv, tot / ppl], axis=1).dropna().corr(method='spearman').iloc[0, 1]})
    gdf = pd.DataFrame(hh_rows + gen)
    cdf = pd.DataFrame(comp)
    tables = {'generation': gdf, 'composition_category': cdf,
              'composition_group': cdf.groupby(['area', 'source', 'group'], as_index=False)['wt_pct'].sum(),
              'income': pd.DataFrame(inc), 'sensitivity': pd.DataFrame(sens), 'data_issues': pd.DataFrame(ISSUES),
              'flows_household_t_day': pd.DataFrame(flows),
              'adjustments': pd.DataFrame(cfg.get('adjustments', []))}
    for k, v in tables.items():
        v.to_csv(os.path.join(out_dir, f'{k}.csv'), index=False)
    write_summary(cfg, tables, out_dir)
    return tables


def md(df, index=True):
    """Markdown table without the optional 'tabulate' dependency."""
    d = df.reset_index() if index else df
    cols = [str(c) for c in d.columns]
    rows = ['| ' + ' | '.join(cols) + ' |', '|' + '---|' * len(cols)]
    for _, r in d.iterrows():
        rows.append('| ' + ' | '.join(fmt(v) if isinstance(v, float) else str(v) for v in r) + ' |')
    return '\n'.join(rows)


def fmt(x, n=3):
    return '' if x is None or (isinstance(x, float) and math.isnan(x)) else (f'{x:.{n}f}' if isinstance(x, float) else str(x))


def write_summary(cfg, t, out_dir):
    g = t['generation'][t['generation']['source'] == 'household']
    L = ['# Waste audit summary', '', '## Household generation', '',
         '| Area | Households | kg/hh/day | kg/cap/day (ratio of totals) | 95% CI | kg/cap/day (mean of ratios) | Adjustment | Adjusted | Household t/day |',
         '|---|---|---|---|---|---|---|---|---|']
    for _, r in g.iterrows():
        L.append(f"| {r['area']} | {int(r['households'])} | {fmt(r['kg_hh_day'])} | {fmt(r.get('kg_cap_day_ratio_of_totals'))} | "
                 f"{fmt(r.get('ci95_low'))}-{fmt(r.get('ci95_high'))} | {fmt(r.get('kg_cap_day_mean_of_ratios'))} | "
                 f"{fmt(r.get('adjustment_kg_cap_day'))} | {fmt(r.get('kg_cap_day_adjusted'))} | {fmt(r.get('household_t_day'), 1)} |")
    L += ['', 'Two per-capita averages are shown on purpose: they differ when household size varies, and reports quote either.', '',
          '## Composition by material group (household, weight %)', '']
    cg = t['composition_group']
    cg = cg[cg['source'] == 'household'].pivot(index='group', columns='area', values='wt_pct').round(1).astype(str)
    L += [md(cg), '']
    fl = t['flows_household_t_day']
    if not fl.empty:
        rec = fl[fl['recyclable']].groupby('area')[['t_day_measured', 't_day_with_adjustments']].sum()
        L += ['## What a sorting facility would receive from households (t/day, recyclable groups)', '', md(rec), '',
              'Per group in `flows_household_t_day.csv`. Non-household sources are added only when unit counts exist.', '']
    nh = t['generation'][t['generation']['source'] != 'household']
    if not nh.empty:
        nh = nh[['area', 'source', 'units_sampled', 'kg_unit_day']].copy()
        nh['note'] = ['indicative only, fewer than 3 units' if n < 3 else '' for n in nh['units_sampled']]
        L += ['## Non-household sources (kg per unit per day)', '', md(nh, index=False), '']
    inc = t['income']
    L += ['## By income group', '', md(inc, index=False) if not inc.empty else
          'Not reported: no income band definitions were supplied, and none were invented.', '']
    if not t['adjustments'].empty:
        L += ['## Adjustments (applied on top of measured data)', '', md(t['adjustments'], index=False), '']
    L += ['## Data-quality log', '', md(t['data_issues'], index=False) if not t['data_issues'].empty else 'None found.', '',
          '## Sensitivity', '', md(t['sensitivity'], index=False) if not t['sensitivity'].empty else '', '']
    with open(os.path.join(out_dir, 'summary.md'), 'w', encoding='utf-8') as f:
        f.write('\n'.join(L))


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('config')
    ap.add_argument('--out', default='results')
    ap.add_argument('--checks-only', action='store_true')
    args = ap.parse_args()
    cfg = json.load(open(args.config, encoding='utf-8'))
    base = os.path.dirname(os.path.abspath(args.config))
    for a in cfg['areas']:
        a['file'] = os.path.join(base, a['file']) if not os.path.isabs(a['file']) else a['file']
    if args.checks_only:
        for a in cfg['areas']:
            preflight(cfg, a, load_area(cfg, a))
        print(md(pd.DataFrame(ISSUES), index=False) if ISSUES else 'No issues found.')
    else:
        analyse(cfg, args.out)
        print(open(os.path.join(args.out, 'summary.md'), encoding='utf-8').read())
