"""Repository consistency checks (no web stack needed): versioning, secrets, CSP-safe frontend."""
import os
import re
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def read(*p):
    with open(os.path.join(ROOT, *p), encoding='utf-8') as f:
        return f.read()


class RepoTests(unittest.TestCase):
    def test_single_version_source(self):
        v = read('VERSION').strip()
        self.assertRegex(v, r'^\d+\.\d+\.\d+$')
        self.assertRegex(read('CHANGELOG.md'), rf'##\s*\[?{re.escape(v)}\]?')
        self.assertIn(f'v{v}', read('README.md'))
        app = read('backend', 'app.py')
        self.assertIn("(ROOT / 'VERSION').read_text()", app)
        self.assertEqual(re.findall(r"['\"]\d+\.\d+\.\d+['\"]", app), [], 'hard-coded version string in app.py')
        self.assertIn('COPY VERSION', read('Dockerfile'))

    def test_no_default_credentials_anywhere(self):
        banned = ['ChangeMe123', 'dev-only-change-this-secret', 'CHANGE_ME']
        for dirpath, _, files in os.walk(ROOT):
            if any(x in dirpath for x in ('.git', '__pycache__', 'node_modules')):
                continue
            for f in files:
                if f.endswith(('.py', '.js', '.html', '.yml', '.yaml', '.md', '.example', '.txt')) and f != 'test_repo.py':
                    text = read(os.path.relpath(os.path.join(dirpath, f), ROOT))
                    for b in banned:
                        self.assertNotIn(b, text, f'{b} found in {f}')

    def test_env_example_has_no_secret_values(self):
        for line in read('.env.example').splitlines():
            m = re.match(r'^(JWT_SECRET|ADMIN_PASSWORD|POSTGRES_PASSWORD|DEMO_PASSWORD|OPENAI_API_KEY)=(\S*)', line)
            if m:
                self.assertEqual(m.group(2), '', f'{m.group(1)} must be blank in .env.example')

    def test_frontend_is_csp_safe(self):
        html, js = read('frontend', 'index.html'), read('frontend', 'app.js')
        self.assertNotRegex(html, r'\son\w+\s*=')
        self.assertNotRegex(html, r'<script(?![^>]*\bsrc=)')
        self.assertNotIn('onclick=', js)
        self.assertNotIn('localStorage', js)  # token lives in sessionStorage only
        self.assertNotRegex(html, r'value="admin"')

    def test_required_files_exist(self):
        for f in ('requirements.txt', 'requirements-dev.txt', 'Dockerfile', 'docker-compose.yml', 'render.yaml',
                  '.github/workflows/ci.yml', '.github/workflows/docker.yml', 'docs/GITHUB_DEPLOY_CHECKLIST.md',
                  'scripts/smoke_test.py', 'demo_data/business_plan_demo.txt'):
            self.assertTrue(os.path.exists(os.path.join(ROOT, f)), f)

    def test_dockerfile_runs_as_non_root(self):
        self.assertRegex(read('Dockerfile'), r'(?m)^USER\s+(?!root)\S+')

    def test_no_postgres_hostile_sql(self):
        self.assertNotIn('=""', read('backend', 'app.py'))  # v1.1 crashed on Postgres with institution_id=""


if __name__ == '__main__':
    unittest.main()
