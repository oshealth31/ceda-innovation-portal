#!/usr/bin/env python3
"""Drive a running portal through the full CEDA idea lifecycle and capture screenshots.

    python scripts/screenshots.py http://localhost:8000 ADMIN_PASSWORD DEMO_PASSWORD out_dir

Sets up data through the API (standard library), then logs in through the real UI with Playwright.
"""
import json
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid
from pathlib import Path

from playwright.sync_api import sync_playwright

BASE, ADMIN_PW, DEMO_PW, OUT = sys.argv[1].rstrip('/'), sys.argv[2], sys.argv[3], Path(sys.argv[4])
OUT.mkdir(parents=True, exist_ok=True)


def call(method, path, token=None, body=None, form=None, file=None):
    headers, data = {}, None
    if token:
        headers['Authorization'] = 'Bearer ' + token
    if body is not None:
        headers['Content-Type'] = 'application/json'
        data = json.dumps(body).encode()
    elif form is not None:
        headers['Content-Type'] = 'application/x-www-form-urlencoded'
        data = urllib.parse.urlencode(form).encode()
    elif file is not None:
        name, content = file
        b = uuid.uuid4().hex
        headers['Content-Type'] = f'multipart/form-data; boundary={b}'
        data = (f'--{b}\r\nContent-Disposition: form-data; name="file"; filename="{name}"\r\n'
                f'Content-Type: text/plain\r\n\r\n').encode() + content + f'\r\n--{b}--\r\n'.encode()
    r = urllib.request.Request(BASE + path, data=data, method=method, headers=headers)
    try:
        with urllib.request.urlopen(r, timeout=60) as resp:
            return json.loads(resp.read() or b'null')
    except urllib.error.HTTPError as e:
        raise SystemExit(f'{method} {path} -> {e.code}: {e.read().decode()[:300]}')


for _ in range(30):
    try:
        call('GET', '/api/health')
        break
    except Exception:
        time.sleep(2)


def login(user, pw):
    return call('POST', '/api/token', form={'username': user, 'password': pw})['access_token']


admin = login('admin', ADMIN_PW)
call('POST', '/api/users', admin, {'username': 'evaluator_thato', 'password': DEMO_PW, 'role': 'officer'})
ids = {u['username']: u['id'] for u in call('GET', '/api/users', admin)}
sub, ev1, ev2, adj = login('applicant1', DEMO_PW), login('officer1', DEMO_PW), login('evaluator_thato', DEMO_PW), login('committee1', DEMO_PW)
prog = call('GET', '/api/programmes', sub)[0]['id']
crit = call('GET', '/api/score-criteria', admin)

DOC = (b'Idea summary\nArtisans in rural Botswana struggle to reach buyers. Our platform lists their crafts online, '
       b'handles mobile-money payments and arranges courier delivery through Botswana Post.\nMarket: tourists, '
       b'export buyers and local gift shops. Team: two developers and a logistics coordinator with experience.\n')


def new_idea(title, problem, solution, users, sector, stage, team):
    a = call('POST', '/api/applications', sub, {'applicant_name': team, 'funding_request': 150000, 'owner_contribution': 20000,
                                                'programme_id': prog, 'idea_title': title, 'problem': problem, 'solution': solution,
                                                'target_users': users, 'sector': sector, 'stage': stage})
    call('POST', f"/api/applications/{a['id']}/analyse-file", sub, file=('idea.txt', DOC))
    return a['id']


def score(token, app_id, values):
    call('PUT', f'/api/applications/{app_id}/scores', token,
         {'scores': [{'criterion_id': c['id'], 'score': values[c['key']], 'comment': values.get('note', '') if c['key'] == 'innovation' else ''}
                     for c in crit]})


# Idea A: awarded journey (two evaluators disagree, referred, awarded)
A = new_idea('Kgotla Crafts: online marketplace for rural artisans', 'Rural artisans cannot reach buyers beyond their village.',
             'A mobile-first marketplace with mobile-money payments and courier delivery.', 'Artisans, tourists, gift shops',
             'Digital and ICT', 'Prototype', 'Kgotla Digital (Pty) Ltd')
call('PUT', f'/api/applications/{A}/assignments', admin, {'reviewer_ids': [ids['officer1'], ids['evaluator_thato']]})
score(ev1, A, {'innovation': 5, 'feasibility': 4, 'impact': 5, 'team': 4, 'alignment': 5, 'note': 'Strong local angle.'})
score(ev2, A, {'innovation': 3, 'feasibility': 2, 'impact': 3, 'team': 3, 'alignment': 4, 'note': 'Courier costs unclear.'})
call('POST', f'/api/applications/{A}/decision', ev1, {'decision': 'refer_committee', 'rationale': 'Scored well overall; panel split on feasibility.'})

# Idea B: sent back for revision with feedback
B = new_idea('AgriSense: soil moisture alerts by SMS', 'Farmers over- or under-water crops and lose yield.',
             'Low-cost soil sensors that send SMS alerts and weekly advice.', 'Smallholder farmers', 'Agriculture', 'Idea',
             'AgriSense Botswana')
call('PUT', f'/api/applications/{B}/assignments', admin, {'reviewer_ids': [ids['officer1']]})
call('POST', f'/api/applications/{B}/decision', ev1, {'decision': 'request_information',
     'rationale': 'Promising idea. Please add the cost of one sensor unit and explain how farmers will pay for SMS alerts.'})

# Idea C: under panel review, waiting for evaluator Thato to score (used for the scoring-form screenshot)
C = new_idea('SafeRide: verified taxi booking for Gaborone', 'Commuters have no way to verify combi and taxi drivers.',
             'A booking app with verified drivers, fare estimates and trip sharing.', 'Commuters and drivers in Gaborone',
             'Transport and logistics', 'Pilot', 'SafeRide Tech')
call('PUT', f'/api/applications/{C}/assignments', admin, {'reviewer_ids': [ids['evaluator_thato']]})

shots = []


def snap(page, name, caption):
    page.wait_for_timeout(700)
    page.screenshot(path=str(OUT / f'{len(shots) + 1:02d}_{name}.png'), full_page=True)
    shots.append({'file': f'{len(shots) + 1:02d}_{name}.png', 'caption': caption})


def ui_login(page, user, pw):
    page.goto(BASE + '/')
    page.evaluate('sessionStorage.clear()')
    page.goto(BASE + '/')
    page.fill('#username', user)
    page.fill('#password', pw)
    page.click('#loginForm button[type=submit]')
    page.wait_for_selector('#portal:not(.hidden)')
    page.wait_for_timeout(600)


def nav(page, name):
    page.click(f'#nav [data-page="{name}"]')
    page.wait_for_timeout(700)


def open_idea(page, title_part):
    nav(page, 'applications')
    page.click(f'tr:has-text("{title_part}") [data-action="open-app"]')
    page.wait_for_selector('#page h2')
    page.wait_for_timeout(700)


with sync_playwright() as p:
    b = p.chromium.launch()
    page = b.new_page(viewport={'width': 1280, 'height': 860})
    page.goto(BASE + '/')
    snap(page, 'login', 'Sign-in page')

    ui_login(page, 'applicant1', DEMO_PW)
    snap(page, 'submitter_dashboard', 'Submitter dashboard: my ideas and their status')
    nav(page, 'new')
    page.fill('input[name=applicant_name]', 'Thuso Solar (Pty) Ltd')
    page.fill('input[name=idea_title]', 'Pay-as-you-go solar kits for rural homes')
    page.fill('textarea[name=problem]', 'Many rural households still rely on paraffin and candles for light.')
    snap(page, 'submit_form', 'Submit an idea: required fields are marked * and checked by the server')
    open_idea(page, 'AgriSense')
    snap(page, 'submitter_sent_back', 'Submitter view of an idea sent back for revision, with the evaluator feedback')
    open_idea(page, 'Kgotla Crafts')
    snap(page, 'submitter_tracking', 'Submitter tracking an idea in adjudication: progress bar and timeline')

    ui_login(page, 'admin', ADMIN_PW)
    snap(page, 'admin_dashboard', 'Administrator dashboard: ideas at every stage')
    open_idea(page, 'SafeRide')
    snap(page, 'admin_assign', 'Administrator assigns evaluators to an idea')

    ui_login(page, 'evaluator_thato', DEMO_PW)
    nav(page, 'applications')
    snap(page, 'evaluator_list', 'Evaluator sees only the ideas assigned to them')
    open_idea(page, 'SafeRide')
    for i, sel in enumerate(page.query_selector_all('form[data-form="scores"] select')):
        sel.select_option(str([4, 4, 5, 3, 4][i % 5]))
    snap(page, 'evaluator_scoring', 'Evaluator scores each criterion from 1 to 5, independently')

    ui_login(page, 'committee1', DEMO_PW)
    nav(page, 'committee')
    snap(page, 'adjudication_queue', 'Adjudication queue')
    open_idea(page, 'Kgotla Crafts')
    snap(page, 'adjudicator_panel', 'Adjudicator sees the panel scores, the disagreement warning and the decision buttons')

    call('POST', f'/api/applications/{A}/decision', adj, {'decision': 'approve', 'rationale': 'Awarded. Strong local impact; agree a courier cost plan in the first month.'})
    ui_login(page, 'applicant1', DEMO_PW)
    open_idea(page, 'Kgotla Crafts')
    snap(page, 'submitter_awarded', 'Submitter sees the award and the adjudicator feedback')

    ui_login(page, 'admin', ADMIN_PW)
    nav(page, 'scoring')
    snap(page, 'scoring_criteria', 'Administrator configures scoring criteria and weights without code changes')
    nav(page, 'management')
    snap(page, 'reports', 'Reporting: status counts and programme KPIs')
    nav(page, 'audit')
    page.click('[data-action="audit-verify"]')
    snap(page, 'audit', 'Tamper-evident audit trail with an integrity check')
    nav(page, 'users')
    snap(page, 'users', 'User management with the four CEDA roles')

    m = b.new_page(viewport={'width': 390, 'height': 844}, device_scale_factor=2, is_mobile=True)
    ui_login(m, 'applicant1', DEMO_PW)
    m.click('[data-action="menu"]') if m.is_visible('[data-action="menu"]') else None
    m.wait_for_timeout(300)
    nav(m, 'applications')
    m.click('tr:has-text("AgriSense") [data-action="open-app"]')
    m.wait_for_timeout(900)
    snap(m, 'mobile', 'The same submitter page on a phone')
    b.close()

(OUT / 'captions.json').write_text(json.dumps(shots, indent=1))
print(f'{len(shots)} screenshots written to {OUT}')
