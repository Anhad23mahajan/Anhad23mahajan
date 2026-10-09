"""Probe the backend API directly with every dataset; writes api_probe.json.
Run: /home/user/work/venv/bin/python -I /home/user/work/ui/scripts/00_api_probe.py
"""
import json, pathlib, httpx, time

BASE = 'http://localhost:8112'
D = pathlib.Path('/home/user/work/ui/data')
out = {}
with httpx.Client(base_url=BASE, timeout=60) as c:
    t = time.time(); r = c.post('/api/demo'); out['demo'] = {'status': r.status_code, 'ms': round((time.time() - t) * 1000), 'bytes': len(r.content)}
    j = r.json()
    out['demo'].update(metric=j['profile']['metric'], date=j['profile']['date'], kpis=j['profile']['kpis'], insights=[i['title'] for i in j['insights']],
                       charts=[(x['type'], x['title'], len(x['x'])) for x in j['charts']], suggested=j['suggested_questions'], ai=j['ai'],
                       summary=j['narrative']['summary'], recs=j['narrative']['recommendations'], metric_cols=j['profile']['metric_cols'], date_cols=j['profile']['date_cols'])
    for f in sorted(D.iterdir()):
        t = time.time()
        r = c.post('/api/upload', files={'file': (f.name, f.read_bytes())})
        e = {'status': r.status_code, 'ms': round((time.time() - t) * 1000), 'bytes': len(r.content)}
        try: j = r.json()
        except Exception: j = {}
        if r.status_code == 200:
            p = j['profile']
            e.update(rows=p['rows'], metric=p['metric'], date=p['date'], kpis=p['kpis'], metric_cols=p['metric_cols'], date_cols=p['date_cols'], cat_cols=p['cat_cols'],
                     insights=[i['title'] for i in j['insights']], charts=[(x['type'], x['title'], len(x['x'])) for x in j['charts']],
                     suggested=j['suggested_questions'], raw_first=j['raw_preview']['rows'][:3], clean_first=j['processed_preview']['rows'][:3],
                     raw_cols=j['raw_preview']['columns'], clean_cols=j['processed_preview']['columns'], dtypes=j['processed_preview']['dtypes'],
                     summary=j['narrative']['summary'], recs=j['narrative']['recommendations'])
        else:
            e['detail'] = j.get('detail', r.text[:200])
        out[f.name] = e
    # ask without key
    sid = c.post('/api/demo').json()['session_id']
    r = c.post('/api/ask', json={'session_id': sid, 'question': 'hi'}); out['ask_no_key'] = {'status': r.status_code, 'body': r.json()}
    r = c.post('/api/ask', json={'session_id': 'deadbeef', 'question': 'hi'}); out['ask_expired'] = {'status': r.status_code, 'body': r.json()}
    r = c.post('/api/forecast', json={'session_id': 'deadbeef', 'date_col': 'a', 'value_col': 'b', 'periods': 6}); out['forecast_expired'] = {'status': r.status_code, 'body': r.json()}
    r = c.post('/api/forecast', json={'session_id': sid, 'date_col': 'order_date', 'value_col': 'amount', 'periods': 2.5}); out['forecast_float_periods'] = {'status': r.status_code, 'body': r.json()}
    r = c.post('/api/forecast', json={'session_id': sid, 'date_col': 'order_date', 'value_col': 'amount', 'periods': 0}); out['forecast_zero_periods'] = {'status': r.status_code, 'note': r.json()['note']}
    r = c.post('/api/forecast', json={'session_id': sid, 'date_col': 'order_date', 'value_col': 'amount', 'periods': 100}); out['forecast_100_periods'] = {'status': r.status_code, 'note': r.json()['note']}
    r = c.get('/favicon.ico'); out['favicon'] = r.status_code
    r = c.get('/assets/index.html'); out['assets_index'] = r.status_code
    r = c.get('/'); out['index_headers'] = dict(r.headers)
pathlib.Path('/home/user/work/ui/api_probe.json').write_text(json.dumps(out, indent=1, default=str))
for k, v in out.items():
    s = {kk: vv for kk, vv in v.items() if kk in ('status', 'ms', 'bytes', 'rows', 'metric', 'date', 'detail')} if isinstance(v, dict) else v
    print(k, s)
