#!/usr/bin/env python3
"""Post-deploy smoke test (standard library only).

    python scripts/smoke_test.py https://your-app.onrender.com officer1 'DEMO_PASSWORD' committee1
"""
import json, sys, time, urllib.error, urllib.parse, urllib.request

base = sys.argv[1].rstrip('/')
user, pw = sys.argv[2], sys.argv[3]
committee = sys.argv[4] if len(sys.argv) > 4 else None
fails = 0


def call(path, token=None, data=None, method=None, raw=False):
    req = urllib.request.Request(base + path, method=method or ('POST' if data is not None else 'GET'))
    if token:
        req.add_header('Authorization', 'Bearer ' + token)
    body = None
    if data is not None:
        body = urllib.parse.urlencode(data).encode()
        req.add_header('Content-Type', 'application/x-www-form-urlencoded')
    with urllib.request.urlopen(req, body, timeout=60) as r:
        out = r.read()
        return (r.status, out, dict(r.headers)) if raw else (r.status, json.loads(out))


def check(name, ok, extra=''):
    global fails
    print(('PASS ' if ok else 'FAIL ') + name + (f'  {extra}' if extra else ''))
    fails += 0 if ok else 1


for attempt in range(12):  # free hosting tiers can take a minute to wake up
    try:
        code, h = call('/api/health')
        break
    except Exception as e:
        print('waiting for service...', type(e).__name__)
        time.sleep(10)
else:
    sys.exit('service did not come up')
check('health', code == 200 and h['status'] == 'ok', h.get('version'))
code, ready = call('/api/health/ready')
check('ready (database reachable)', ready['status'] == 'ready')
_, page, hdrs = call('/', raw=True)
check('portal served', b'Innovation Management Portal' in page)
check('CSP header present', 'content-security-policy' in {k.lower() for k in hdrs})  # header names are case-insensitive
try:
    call('/api/applications')
    check('API rejects anonymous', False)
except urllib.error.HTTPError as e:
    check('API rejects anonymous', e.code == 401)
code, tok = call('/api/token', data={'username': user, 'password': pw})
token = tok['access_token']
check('login', code == 200 and tok['role'] in ('officer', 'admin'), tok['role'])
code, apps = call('/api/applications', token)
check('applications list', code == 200 and apps['total'] >= 1, f"{apps['total']} application(s)")
demo = next((a for a in apps['items'] if 'Demo' in a['applicant_name']), None)
check('demo application present', demo is not None)
if demo:
    code, full = call('/api/applications/' + demo['id'], token)
    a = full['assessment']
    check('assessment has rubric', bool(a and a['rubric']['criteria']), f"coverage {a['rubric']['coverage_pct']}%")
    check('revenue extracted correctly', a['metrics']['revenue'] == 1200000)
    code, html, _ = call(f"/api/applications/{demo['id']}/committee-report", token, raw=True)
    check('committee report (authenticated)', code == 200 and b'Committee Assessment Report' in html)
    code, docx, _ = call(f"/api/applications/{demo['id']}/committee-report.docx", token, raw=True)
    check('Word report', docx[:2] == b'PK')
if committee:
    code, t2 = call('/api/token', data={'username': committee, 'password': pw})
    check('committee login', t2['role'] == 'committee')
print('\nALL CHECKS PASSED' if not fails else f'\n{fails} CHECK(S) FAILED')
sys.exit(1 if fails else 0)
