"""Local-only audit. Run against an isolated DB, never a public deployment."""
import argparse
import hashlib
import json
import re
import sys
import uuid
import secrets
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit, urljoin
import requests

ROOT = Path(__file__).resolve().parents[1]

class Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []
    def handle_starttag(self, tag, attrs):
        for key, value in attrs:
            if key in ('href', 'src') and value:
                self.links.append(value)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--base', default='http://127.0.0.1:8019')
    args = parser.parse_args()
    if urlsplit(args.base).hostname not in ('127.0.0.1', 'localhost'):
        raise SystemExit('LOCAL_ONLY')
    out = ROOT / 'audit_artifacts'
    out.mkdir(exist_ok=True)
    results = []
    def check(name, passed, evidence=''):
        results.append(dict(test=name, status='PASS' if passed else 'FAIL', evidence=evidence))
    s = requests.Session()
    s.trust_env = False
    def get(path):
        return s.get(args.base + path, timeout=10)
    def post(path, payload):
        return s.post(args.base + '/api/auth/' + path, json=payload, timeout=10)
    pages = sorted((ROOT / 'public').glob('*.html'))
    refs = set()
    for page in pages:
        r = get('/' + page.name)
        check('page:' + page.name, r.status_code == 200 and '<html' in r.text)
        links = Links(); links.feed(page.read_text(encoding='utf-8-sig'))
        for value in links.links:
            if not value.startswith('#'):
                refs.add(urljoin('/' + page.name, value))
    check('homepage', get('/').status_code == 200)
    economy = (ROOT / 'public/human.html').read_text(encoding='utf-8-sig')
    allocations = [int(x) for x in re.findall(r'<td>(\d+)%</td>', economy)]
    check('content:allocation_verified_or_withheld', (bool(allocations) and sum(allocations) == 100) or (not allocations and 'UNVERIFIED' in economy and 'withheld' in economy), str(sum(allocations)))
    check('content:economy_source_matches_public', (ROOT / 'human.html').read_bytes() == (ROOT / 'public/human.html').read_bytes(), 'Owner must select the approved allocation; audit does not invent percentages.')
    for ref in sorted(refs):
        if not urlsplit(ref).scheme:
            check('link:' + ref, get(ref).status_code == 200)
    for path in ['/assets/razviton-token.svg', '/assets/razviton-token.png', '/token/metadata.json']:
        check('asset:' + path, get(path).status_code == 200)
    for path in ['/.git/config', '/backend/app/main.py', '/backend/data/razviton.db', '/.env', '/assets/', '/%2e%2e/backend/app/main.py', '/docs', '/openapi.json']:
        check('not_exposed:' + path, get(path).status_code in (400, 404))
    check('health', get('/health').json().get('status') == 'ok')
    r = get('/api/auth/me')
    check('anonymous_me', r.status_code == 401)
    check('api_no_store', r.headers.get('Cache-Control') == 'no-store')
    check('anonymous_admin', get('/api/auth/admin/stats').status_code == 401)
    ident = 'Audit_' + uuid.uuid4().hex[:12]
    payload = dict(username=ident, email=ident.lower()+'@example.invalid', password=secrets.token_urlsafe(24), full_name='<img src=x onerror=alert(1)>')
    r = post('register', payload)
    check('register', r.status_code == 200)
    check('http_only_cookie', 'httponly' in r.headers.get('set-cookie', '').lower())
    check('same_site_cookie', 'samesite=lax' in r.headers.get('set-cookie', '').lower())
    check('me_after_register', get('/api/auth/me').status_code == 200)
    check('non_admin_forbidden', get('/api/auth/admin/stats').status_code == 403)
    check('duplicate_register', post('register', payload).status_code == 409)
    r = post('register', dict(payload, username=ident.lower()))
    check('case_duplicate', r.status_code == 409)
    check('spaces_username', post('register', dict(payload, username='   ', email='spaces-'+payload['email'])).status_code == 422)
    r = post('login', dict(identifier=payload['email'], password='short'))
    check('short_password_validation', r.status_code == 422)
    check('validation_no_input_echo', 'short' not in r.text and 'input' not in r.json())
    check('logout', post('logout', {'all_devices': False}).status_code == 200)
    check('session_revoked', get('/api/auth/me').status_code == 401)
    check('wrong_password', post('login', dict(identifier=ident, password='NotTheCorrect123')).status_code == 401)
    check('mixed_case_username_login', post('login', dict(identifier=ident.upper(), password=payload['password'])).status_code == 200)
    check('logout_all_devices', post('logout', {'all_devices': True}).status_code == 200)
    check('email_login', post('login', dict(identifier=payload['email'].upper(), password=payload['password'])).status_code == 200)
    check('sql_injection_rejected', post('login', dict(identifier="' OR 1=1 --", password='NotTheCorrect123')).status_code == 401)
    r = get('/')
    for key in ['X-Content-Type-Options','X-Frame-Options','Referrer-Policy','Content-Security-Policy']:
        check('header:' + key, bool(r.headers.get(key)))
    codes = [post('login', dict(identifier='no-such-audit-user',password='NotTheCorrect123')).status_code for _ in range(32)]
    check('rate_limit_429', 429 in codes)
    inventory = []
    secret_hits = []
    patterns = {
        'PRIVATE_KEY': r'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----',
        'GITHUB_TOKEN': r'\b(?:gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{40,})\b',
        'AWS_ID': r'\bAKIA[A-Z0-9]{16}\b',
        'TOKEN': r'\bsk-[A-Za-z0-9_-]{24,}\b',
        'TELEGRAM': r'\b[0-9]{8,12}:[A-Za-z0-9_-]{32,}\b',
        'PRIVATE_ASSIGNMENT': r'(?i)(?:api_key|private_key|seed_phrase|mnemonic|database_password)\s*[:=]\s*[\"\x27][^\"\x27]{8,}[\"\x27]',
    }
    for p in sorted(ROOT.rglob('*')):
        if not p.is_file() or any(x in p.parts for x in ('.git','__pycache__','audit_artifacts','.venv','node_modules','data')):
            continue
        raw = p.read_bytes()
        rel = p.relative_to(ROOT).as_posix()
        inventory.append(dict(file=rel, bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest()))
        if p.suffix != '.png':
            text = raw.decode('utf-8-sig', errors='replace')
            for kind, pattern in patterns.items():
                for match in re.finditer(pattern, text):
                    secret_hits.append(dict(file=rel, line=text[:match.start()].count('\n')+1, type=kind))
    data = dict(timestamp=datetime.now(timezone.utc).isoformat(), base=args.base, tests=results, pages=len(pages), internal_refs=len(refs), inventory=inventory, secret_candidates=secret_hits)
    (out/'smoke.json').write_text(json.dumps(data, indent=2), encoding='utf-8')
    print(json.dumps(dict(pass_count=sum(x['status']=='PASS' for x in results),fail_count=sum(x['status']=='FAIL' for x in results),pages=len(pages),files=len(inventory),secret_candidates=secret_hits)))
    for test in results:
        if test['status']=='FAIL': print(json.dumps(test))
    return int(any(x['status']=='FAIL' for x in results))

if __name__ == '__main__':
    sys.exit(main())
