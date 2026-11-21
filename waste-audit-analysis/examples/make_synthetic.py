#!/usr/bin/env python3
"""Build a synthetic two-area waste audit with planted problems and a known answer.

Writes examples/synthetic/{riverside,hillside}.csv, ANSWER.json (truth plus the list of planted problems).
The data is invented. It mimics the shape of real tally sheets: note rows at the top, household rows,
then a few non-household units.
"""
import csv, json, os, random

rng = random.Random(42)
HERE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'synthetic')
os.makedirs(HERE, exist_ok=True)
CATS = {'kitchen': 'organic', 'garden': 'organic', 'manure': 'organic', 'plastic_bag': 'plastic', 'sachet': 'plastic',
        'pet_bottle': 'plastic', 'paper': 'paper', 'glass': 'glass', 'metal': 'metal', 'diapers': 'other', 'other': 'other'}
# daily kg per person, means (under-captured organics on purpose: total about 0.12)
MEAN = {'kitchen': .045, 'garden': .02, 'manure': 0, 'plastic_bag': .008, 'sachet': .006, 'pet_bottle': .002,
        'paper': .015, 'glass': .001, 'metal': .001, 'diapers': .006, 'other': .004}
DAYS = 7
truth = {}
planted = []


def household(people):
    return {c: round(max(0, rng.gauss(m, m * .5)) * people * DAYS, 3) for c, m in MEAN.items()}


for area, unit in [('riverside', 'kg'), ('hillside', 'g')]:
    rows = []
    for i in range(1, 121):
        p = rng.choice([2, 3, 3, 4, 4, 4, 5, 5, 6, 7])
        w = household(p)
        rows.append({'id': f'{area[0].upper()}{i:03d}', 'type': 'household', 'people': p,
                     'income_idr': rng.choice([500000, 750000, 900000, 1100000, 1500000, 2000000, 3500000]), **w})
    # truth on clean data, before any planted problem
    kg = sum(sum(r[c] for c in CATS) for r in rows) / DAYS
    ppl = sum(r['people'] for r in rows)
    truth[area] = {'households': len(rows), 'kg_cap_day': round(kg / ppl, 4), 'kg_hh_day': round(kg / len(rows), 4)}
    # planted problems
    if area == 'riverside':
        rows[10]['people'] = 4.2; rows[47]['people'] = 4.2
        planted.append('riverside: two household sizes typed as 4.2 (a mean filled in for missing values)')
        rows.append(dict(rows[20], id='R121'))
        planted.append('riverside: row R121 duplicates R021 (copy-paste); 121 rows for 120 households')
        rows[70]['kitchen'] = round(rows[70]['kitchen'] * 12, 3)
        planted.append('riverside: R071 kitchen waste is 12x typical (outlier, likely a typing error)')
        rows[33]['paper'] = str(rows[33]['paper']).replace('.', ',')
        planted.append('riverside: R034 paper weight typed with a decimal comma (text, not a number)')
    else:
        planted.append('hillside: all weights in grams (header note), riverside in kg')
        rows[5]['income_idr'] = 'n/a'; rows[6]['income_idr'] = 'n/a'
        planted.append('hillside: two households with income "n/a"')
    for r in rows:
        if area == 'hillside':
            for c in CATS:
                r[c] = round(r[c] * 1000)
    nh = [{'id': f'{area[0].upper()}N{j}', 'type': t, 'people': '', 'income_idr': '',
           **{c: round(max(0, rng.gauss(MEAN[c] * 40, MEAN[c] * 15)) * DAYS * (1000 if area == 'hillside' else 1), 3) for c in CATS}}
          for j, t in enumerate(['school', 'shop', 'shop', 'market stall', 'health post'], 1)]
    with open(os.path.join(HERE, f'{area}.csv'), 'w', newline='', encoding='utf-8') as f:
        w = csv.writer(f)
        w.writerow([f'# Waste audit tally, {area} ward. Weights in {"kilograms" if unit == "kg" else "grams"} per category, '
                    f'summed over the {DAYS} days analysed (8 days collected, day 1 discarded).'])
        w.writerow(['# Population of ward: ' + ('41,200' if area == 'riverside' else '28,900')])
        cols = ['id', 'type', 'people', 'income_idr'] + list(CATS)
        w.writerow(cols)
        for r in rows + nh:
            w.writerow([r[c] for c in cols])
planted += ['both: manure is zero in every household (category not present or not sorted)',
            'both: generation about 0.12 kg/cap/day, far below typical Indonesian or SE Asian references (organics under-captured)',
            'both: non-household units sampled, but no counts of schools, shops, stalls or health posts in the wards',
            'both: no container volumes, so density cannot be computed']
json.dump({'truth_clean_data': truth, 'planted_problems': planted, 'days': DAYS}, open(os.path.join(HERE, 'ANSWER.json'), 'w'), indent=2)
print(json.dumps(truth, indent=2))
