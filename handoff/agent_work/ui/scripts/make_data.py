"""Generate the test / sample datasets used by the QA scripts (deterministic).

Run:  /home/user/work/ui/pwvenv/bin/python -I /home/user/work/ui/scripts/make_data.py
Needs numpy+pandas -> uses the backend venv:  /home/user/work/venv/bin/python
"""
import pathlib, numpy as np, pandas as pd

OUT = pathlib.Path('/home/user/work/ui/data'); OUT.mkdir(parents=True, exist_ok=True)
SAMPLES = pathlib.Path('/home/user/work/ui/snippets/samples'); SAMPLES.mkdir(parents=True, exist_ok=True)
rng = np.random.default_rng(23)

# ---------------------------------------------------------------- donations (also shipped as a sample)
camps = {'Annual Appeal': .30, 'Giving Tuesday': .12, 'Spring Gala': .14, 'Monthly Giving': .26, 'School Supplies Drive': .10, 'Emergency Relief': .08}
chans = {'Online': .52, 'Event': .18, 'Mail': .12, 'Corporate': .06, 'Phone': .12}
names = [f'{a} {b}' for a in ['Maya', 'Liam', 'Noor', 'Ethan', 'Sofia', 'Arjun', 'Chloe', 'Omar', 'Priya', 'Lucas', 'Amara', 'Diego', 'Hana', 'Jonas', 'Leila']
         for b in ['Patel', 'Nguyen', 'Garcia', 'Okafor', 'Smith', 'Kim', 'Rossi', 'Haddad']]
rows = []
for d in pd.date_range('2023-01-01', '2025-09-30'):
    m = d.month
    season = {11: 1.6, 12: 2.6, 1: .9, 3: 1.1, 4: 1.2}.get(m, 1.0)
    grow = 1 + (d - pd.Timestamp('2023-01-01')).days / 1000
    n = rng.poisson(1.5 * season * grow * (1.2 if d.dayofweek in (1, 2) else 1))
    if d == pd.Timestamp('2024-11-26'): n += 18                               # Giving Tuesday
    for _ in range(n):
        camp = rng.choice(list(camps), p=np.array(list(camps.values())) / sum(camps.values()))
        if d == pd.Timestamp('2024-11-26'): camp = 'Giving Tuesday'
        ch = rng.choice(list(chans), p=np.array(list(chans.values())) / sum(chans.values()))
        amt = float(np.round(rng.lognormal(3.6, .8), 2)) if camp != 'Monthly Giving' else float(rng.choice([10, 15, 25, 50]))
        rows.append([d.strftime('%Y-%m-%d'), rng.choice(names), camp, ch, amt, 'Yes' if camp == 'Monthly Giving' else 'No'])
don = pd.DataFrame(rows, columns=['Date', 'Donor Name', 'Campaign', 'Channel', 'Amount (USD)', 'Recurring'])
big = don.index[(don['Date'] >= '2024-12-10')][0]
don.loc[big, ['Amount (USD)', 'Donor Name', 'Channel', 'Campaign']] = [25000.0, 'Brightfield Foundation', 'Corporate', 'Annual Appeal']   # one big year-end gift (outlier)
don.loc[don.sample(frac=.06, random_state=1).index, 'Channel'] = np.nan
don['Notes'] = pd.Series(np.where(rng.random(len(don)) < .12, None, 'Thank-you sent'), dtype=object)                                           # 12% empty (below the 20% warning threshold)
don.to_csv(OUT / 'donations.csv', index=False)
don.to_csv(SAMPLES / 'donations.csv', index=False)

# ---------------------------------------------------------------- inventory (sample #3)
prods = {'Rice 25kg': ('Pantry', 31), 'Canned beans': ('Pantry', 1.2), 'Olive oil 5L': ('Pantry', 22), 'Blankets': ('Winter', 9),
         'Winter coats': ('Winter', 28), 'Hygiene kits': ('Health', 6.5), 'First-aid kits': ('Health', 14), 'School bags': ('Education', 8)}
wh = ['Central', 'North depot', 'Harbour']
inv = []
for d in pd.date_range('2024-01-01', '2025-06-30', freq='W-MON'):
    for p, (cat, cost) in prods.items():
        for w in wh:
            seas = 1.8 if (cat == 'Winter' and d.month in (10, 11, 12, 1)) else 1.0
            u = int(max(0, rng.normal(40 * seas, 12)))
            inv.append([d.strftime('%Y-%m-%d'), p, cat, w, u, round(u * cost, 2), cost, int(max(0, rng.normal(200, 60)))])
pd.DataFrame(inv, columns=['week', 'product', 'category', 'warehouse', 'units_shipped', 'cost', 'unit_price', 'stock_on_hand']).to_csv(SAMPLES / 'inventory.csv', index=False)

# ---------------------------------------------------------------- messy European CSV (latin-1, ; sep, decimal comma, dd.mm.yyyy)
eu = []
cats = {'Käse': 8.9, 'Brötchen': .65, 'Müsli': 4.2, 'Café crème': 3.5, 'Süßwaren': 2.1}
for d in pd.date_range('2025-01-01', '2025-09-30', freq='2D'):
    for p, price in cats.items():
        q = int(rng.integers(5, 140))
        eu.append([d.strftime('%d.%m.%Y'), p, 'Zürich' if rng.random() < .5 else 'München', q, price * q])
lines = ['Datum;Produkt;Filiale;Menge;Umsatz (€)']
for r in eu:
    umsatz = f"{r[4]:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.') + ' €'      # 1.234,56 €
    lines.append(f"{r[0]};{r[1]};{r[2]};{r[3]};{umsatz}")
lines.insert(3, '')                                                                           # blank line mid-file
lines.insert(6, ';;;;')                                                                       # blank row
lines[10] = lines[10].rsplit(';', 1)[0] + ';n/a'                                              # a missing value
(OUT / 'messy_european.csv').write_bytes('\n'.join(lines).encode('cp1252'))

# ---------------------------------------------------------------- edge cases
(OUT / 'bad_file.csv').write_bytes(bytes(range(256)) * 20)                                    # binary junk
(OUT / 'not_data.txt').write_text('hello world, this is just a sentence.\n')
(OUT / 'empty.csv').write_text('')
(OUT / 'header_only.csv').write_text('date,amount\n')

# no dates -> forecast disabled, no line chart
nd = pd.DataFrame({'region': rng.choice(['N', 'S', 'E', 'W'], 200), 'amount': rng.integers(5, 500, 200), 'rating': rng.integers(1, 6, 200)})
nd.to_csv(OUT / 'no_dates.csv', index=False)

# very few signals: random noise, no metric hints -> "empty insights" state
pd.DataFrame({'note': [f'row {i}' for i in range(30)], 'comment': ['x'] * 30}).to_csv(OUT / 'text_only.csv', index=False)
pd.DataFrame({'id': range(1, 41), 'name': [f'item {i}' for i in range(40)], 'colour': rng.choice(['red', 'blue'], 40)}).to_csv(OUT / 'no_insights.csv', index=False)

# negatives + many categories + long labels + date-like category
ex = []
longcats = [f'Operations / {x} programme and community partnerships fund' for x in
            ['Housing', 'Food security', 'Youth education', 'Elder care', 'Mental health', 'Legal aid', 'Job training', 'Transport', 'Sports', 'Arts', 'Energy', 'Water']]
for d in pd.date_range('2024-01-01', '2025-06-30', freq='5D'):
    for c in longcats:
        ex.append([d.strftime('%Y-%m-%d'), c, round(float(rng.normal(300, 900)), 2), 'FY2024-25' if d.year == 2024 or d.month < 7 else 'FY2025-26'])
pd.DataFrame(ex, columns=['transaction_date', 'program', 'net_amount', 'fiscal_year']).to_csv(OUT / 'negatives_long_labels.csv', index=False)

# 40 categories (pie / bar stress) -- starter charts cap at 30 unique, so use 28
mc = [f'Category {i:02d}' for i in range(28)]
mcd = pd.DataFrame({'order_date': pd.date_range('2024-01-01', periods=300, freq='D').strftime('%Y-%m-%d'),
                    'category': rng.choice(mc, 300), 'amount': rng.integers(10, 900, 300)})
mcd.to_csv(OUT / 'many_categories.csv', index=False)

# short history (<8 periods): forecast error
pd.DataFrame({'order_date': pd.date_range('2025-01-01', periods=6, freq='D').strftime('%Y-%m-%d'), 'region': rng.choice(['N', 'S'], 6), 'amount': rng.integers(10, 99, 6)}).to_csv(OUT / 'short_history.csv', index=False)

# small-valued metric (rates / averages) -> hover/label rounding
sm = pd.DataFrame({'order_date': pd.date_range('2024-01-01', periods=400, freq='D').strftime('%Y-%m-%d'),
                   'channel': rng.choice(['Email', 'Social', 'Search', 'Referral'], 400), 'conversion_rate': np.round(rng.uniform(.01, .09, 400), 4)})
sm.to_csv(OUT / 'small_rates.csv', index=False)

# html / injection payloads in cell values
inj = pd.DataFrame({'order_date': pd.date_range('2024-01-01', periods=120, freq='D').strftime('%Y-%m-%d'),
                    'category': rng.choice(['<img src=x onerror="window.__xss=1">', "O'Brien \" & <b>Sons</b>", '</script><script>window.__xss=2</script>', '<a href="javascript:window.__xss=3">link</a>'], 120),
                    'amount': rng.integers(10, 900, 120)})
inj.to_csv(OUT / 'injection.csv', index=False)

# dates but no numeric column
pd.DataFrame({'order_date': pd.date_range('2024-01-01', periods=40, freq='D').strftime('%Y-%m-%d'), 'region': rng.choice(['N', 'S', 'E'], 40)}).to_csv(OUT / 'dates_no_metric.csv', index=False)

print('ok', sorted(p.name for p in OUT.iterdir()), sorted(p.name for p in SAMPLES.iterdir()))
