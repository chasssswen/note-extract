"""Validate anonymous-first extraction and the browser-confirmed retry boundary."""
import contextlib
import importlib.util
import io
import json
import sys
import tempfile
from types import SimpleNamespace
import unittest
from pathlib import Path
from unittest.mock import patch
from http.cookiejar import CookieJar

sys.dont_write_bytecode = True
SCRIPT = Path(__file__).resolve().parents[1] / 'skills/note-extract/scripts/extract_note.py'
spec = importlib.util.spec_from_file_location('extract_note', SCRIPT)
extract = importlib.util.module_from_spec(spec)
spec.loader.exec_module(extract)
NOTE_ID = 'abcdef0123456789abcdef01'
URL = f'https://www.xiaohongshu.com/explore/{NOTE_ID}'


def note_page():
    note = {'noteId': NOTE_ID, 'title': '测试笔记', 'desc': '正文第一行\n第二行 🌤️\n#天气[话题]#',
            'type': 'normal', 'user': {'nickname': '测试作者'},
            'imageList': [{'fileId': key, 'urlDefault': f'https://test.xhscdn.com/{key}'}
                          for key in ['first', 'second', 'first']]}
    return '<script>window.__INITIAL_STATE__=' + json.dumps(
        {'note': {'noteDetailMap': {NOTE_ID: {'note': note}}}}, ensure_ascii=False) + '</script>'


class AnonymousFirstTests(unittest.TestCase):
    def run_cli(self, args, page=note_page(), cookie_jar=None, cookie_error=None, request_error=None):
        from PIL import Image
        events, blobs = [], {}
        for key, color in [('first', 'blue'), ('second', 'green')]:
            b = io.BytesIO()
            Image.new('RGB', (32, 48), color).save(b, 'PNG')
            blobs[key] = b.getvalue()

        def fake_fetch(address, jar=None, image=False):
            events.append((address, jar, image))
            if image:
                self.assertIsNone(jar, 'CDN downloads must never receive CookieJar')
                return blobs[address.rsplit('/', 1)[-1]], address, 200, 'image/png'
            if request_error:
                raise request_error
            return page.encode(), address, 200, 'text/html'

        with tempfile.TemporaryDirectory() as tmp, patch.object(extract, 'fetch', side_effect=fake_fetch), \
             patch.object(extract, 'browser_cookie_jar', side_effect=cookie_error,
                          return_value=(cookie_jar, {'source': 'mock-browser', 'cookie_count': 0})) as cookie_reader, \
             patch.object(sys, 'argv', ['extract_note.py', '--out', tmp, *args]), \
             contextlib.redirect_stdout(io.StringIO()) as output:
            code = extract.main()
            states = [json.loads(line) for line in output.getvalue().splitlines()]
            exported = list(Path(tmp).rglob('note.json'))
            notes = [json.loads(p.read_text()) for p in exported]
            return code, states, notes, cookie_reader.call_count, events

    def test_anonymous_success_never_reads_browser_cookies(self):
        code, states, notes, reads, events = self.run_cli(['--url', URL])
        self.assertEqual(code, 0)
        self.assertEqual(reads, 0)
        self.assertTrue(all(jar is None for _, jar, _ in events))
        self.assertEqual(notes[0]['authentication']['source'], 'anonymous')
        self.assertEqual(notes[0]['body'], '正文第一行\n第二行 🌤️\n#天气')
        self.assertEqual(len(notes[0]['images']), 2)
        self.assertEqual(notes[0]['validation']['docx_embedding'], 'passed')

    def test_home_shell_requests_login_without_reading_cookies(self):
        code, states, notes, reads, _ = self.run_cli(['--url', URL], page='<html>首页壳页</html>')
        self.assertEqual(code, 2)
        self.assertEqual(reads, 0)
        self.assertEqual(notes, [])
        self.assertEqual(states[0]['code'], 'AUTH_FALLBACK_REQUIRED')

    def test_tls_failure_does_not_request_login(self):
        code, states, _, reads, _ = self.run_cli(['--url', URL], request_error=extract.ExtractError('TLS_CERTIFICATE_ERROR', 'TLS失败'))
        self.assertEqual(code, 1)
        self.assertEqual(reads, 0)
        self.assertEqual(states[0]['code'], 'TLS_CERTIFICATE_ERROR')

    def test_http_401_requests_authenticated_retry(self):
        code, states, _, reads, _ = self.run_cli(['--url', URL], request_error=extract.ExtractError('HTTP_ERROR', 'HTTP 401', http_status=401))
        self.assertEqual(code, 2)
        self.assertEqual(reads, 0)
        self.assertEqual(states[0]['status'], 'auth_required')

    def test_http_404_does_not_request_login(self):
        code, states, _, reads, _ = self.run_cli(['--url', URL], request_error=extract.ExtractError('HTTP_ERROR', 'HTTP 404', http_status=404))
        self.assertEqual(code, 1)
        self.assertEqual(reads, 0)
        self.assertEqual(states[0]['status'], 'failed')

    def test_explicit_retry_uses_cookies_only_for_note_page(self):
        jar = CookieJar()
        code, _, notes, reads, events = self.run_cli(['--authenticated', '--url', URL], cookie_jar=jar)
        self.assertEqual(code, 0)
        self.assertEqual(reads, 1)
        self.assertIs(events[0][1], jar)
        self.assertTrue(all(j is None for _, j, image in events if image))
        self.assertEqual(notes[0]['authentication']['source'], 'mock-browser')

    def test_supplied_cookie_does_not_read_browser(self):
        with patch.object(sys, 'stdin', io.StringIO('web_session=test-fixture-only')):
            code, _, notes, reads, events = self.run_cli(['--authenticated', '--cookie-stdin', '--url', URL])
        self.assertEqual(code, 0)
        self.assertEqual(reads, 0)
        self.assertEqual(notes[0]['authentication']['source'], 'user-supplied-cookie')
        self.assertTrue(all(jar is None for _, jar, image in events if image))

    def test_anonymous_curl_refuses_redirect_before_requesting_unexpected_host(self):
        def redirect(command, **kwargs):
            self.assertEqual(command[:2], ['curl', '-q'])
            self.assertIn('Cookie:', command)
            self.assertNotIn('--location', command)
            Path(command[command.index('--dump-header') + 1]).write_text(
                'HTTP/2 302\nLocation: https://example.com/collect\n')
            return SimpleNamespace(returncode=0, stdout='302\ntext/html')

        with patch.object(extract.subprocess, 'run', side_effect=redirect) as request:
            with self.assertRaises(extract.ExtractError) as result:
                extract.anonymous_fetch_curl(URL)
        self.assertEqual(result.exception.code, 'UNEXPECTED_REDIRECT')
        self.assertEqual(request.call_count, 1)

    def test_cookie_read_failure_is_reported_and_not_repeated_for_batch(self):
        code, states, notes, reads, _ = self.run_cli(
            ['--authenticated', '--url', URL, '--url', URL],
            cookie_error=extract.ExtractError('BROWSER_PERMISSION_DENIED', '系统拒绝读取'))
        self.assertEqual(code, 2)
        self.assertEqual(reads, 1)
        self.assertEqual(notes, [])
        self.assertTrue(all(x['code'] == 'BROWSER_PERMISSION_DENIED' for x in states))

    def test_batch_retains_success_before_requesting_retry(self):
        bad_id = '0123456789abcdef01234567'
        code, states, notes, reads, _ = self.run_cli(['--url', URL, '--url', f'https://www.xiaohongshu.com/explore/{bad_id}'])
        self.assertEqual(code, 2)
        self.assertEqual(reads, 0)
        self.assertEqual(len(notes), 1)
        self.assertEqual(states[0]['status'], 'exported')
        self.assertEqual(states[1]['input_index'], 2)
        self.assertEqual(states[1]['status'], 'auth_required')

    def test_requested_id_survives_redirect_to_home_shell(self):
        with patch.object(extract, 'fetch', return_value=(b'<html>home</html>', 'https://www.xiaohongshu.com/', 200, 'text/html')):
            with self.assertRaises(extract.ExtractError) as result:
                extract.request_note(URL)
            self.assertEqual(result.exception.code, 'NOTE_NOT_FOUND')


if __name__ == '__main__':
    unittest.main()
