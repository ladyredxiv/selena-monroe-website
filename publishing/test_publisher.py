import importlib.util
import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest
from datetime import datetime
from xml.etree import ElementTree as ET

HERE = Path(__file__).resolve().parent
sys.dont_write_bytecode = True
spec = importlib.util.spec_from_file_location('publisher', HERE / 'publish.py')
publisher = importlib.util.module_from_spec(spec)
spec.loader.exec_module(publisher)


class PublisherTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.source = self.root / 'private'
        shutil.copytree(HERE, self.source)
        self.public = self.root / 'public_html'
        self.public.mkdir()
        self.state = self.root / 'state'
        self.post = {
            'slug': 'scheduled-test-entry', 'title': 'A title & its archive',
            'dek': 'Test dek', 'description': 'Test description',
            'date': '2026-11-04', 'displayDate': 'November 4, 2026',
            'category': 'Field Notes', 'readTime': '2 minute read',
            'excerpt': 'A test excerpt.', 'publish_at': '2026-11-04T09:00:00-05:00',
            'approved': True, 'body_html': '<p>Reviewed test text.</p>'
        }

    def tearDown(self):
        self.temp.cleanup()

    def queue(self, posts):
        (self.source / 'queue.json').write_text(json.dumps({'posts': posts}), encoding='utf-8')

    def run_at(self, timestamp, dry=False):
        return publisher.publish(self.source, self.public, self.state,
                                 publisher.instant(timestamp), dry)

    def test_approval_and_release_boundary(self):
        self.queue([self.post])
        self.run_at('2026-11-04T13:59:59+00:00')
        self.assertFalse((self.public / 'archive/scheduled-test-entry/index.html').exists())
        self.assertNotIn(self.post['slug'], (self.public / 'posts.json').read_text(encoding='utf-8'))
        self.post['approved'] = False
        self.queue([self.post])
        self.run_at('2026-11-04T14:00:00+00:00')
        self.assertFalse((self.public / 'archive/scheduled-test-entry/index.html').exists())
        self.post['approved'] = True
        self.queue([self.post])
        self.run_at('2026-11-04T14:00:00+00:00')
        for file in ('index.html', 'archive.html', 'posts.json', 'archive-feed.xml', 'sitemap.xml'):
            self.assertIn(self.post['slug'], (self.public / file).read_text(encoding='utf-8'))
        page = (self.public / 'archive/scheduled-test-entry/index.html').read_text(encoding='utf-8')
        self.assertIn('A title &amp; its archive', page)
        self.assertIn('Reviewed test text', page)
        ET.parse(self.public / 'archive-feed.xml')
        ET.parse(self.public / 'sitemap.xml')
        json.loads(page.split('<script type="application/ld+json">')[1].split('</script>')[0])

    def test_redeploy_restores_published_and_is_idempotent(self):
        self.queue([self.post])
        self.run_at('2026-11-04T14:00:00+00:00')
        before = {str(p.relative_to(self.public)): p.read_bytes()
                  for p in self.public.rglob('*') if p.is_file()}
        self.queue([])
        (self.public / 'index.html').write_text('Older static deployment', encoding='utf-8')
        (self.public / 'archive/scheduled-test-entry/index.html').unlink()
        self.run_at('2026-12-01T14:00:00+00:00')
        after = {str(p.relative_to(self.public)): p.read_bytes()
                 for p in self.public.rglob('*') if p.is_file()}
        self.assertEqual(before, after)
        self.run_at('2026-12-01T14:00:00+00:00')
        self.assertEqual(after, {str(p.relative_to(self.public)): p.read_bytes()
                                for p in self.public.rglob('*') if p.is_file()})

    def test_dry_run_writes_nothing(self):
        self.queue([self.post])
        self.run_at('2026-11-04T14:00:00+00:00', True)
        self.assertEqual(list(self.public.iterdir()), [])
        self.assertFalse(self.state.exists())

    def test_invalid_input_fails_before_writes(self):
        for change in [{'slug': '../escape'}, {'publish_at': '2026-11-04T09:00:00'},
                       {'body_html': ''}]:
            with self.subTest(change=change):
                self.queue([dict(self.post, **change)])
                with self.assertRaises(ValueError):
                    self.run_at('2026-12-01T14:00:00+00:00')
                self.assertEqual(list(self.public.iterdir()), [])

    def test_duplicate_slug_rejected(self):
        self.queue([self.post, self.post])
        with self.assertRaises(ValueError):
            self.run_at('2026-12-01T14:00:00+00:00')

    def test_current_deployment_layout_preserved(self):
        template = self.source / 'templates/index.html'
        template.write_text(template.read_text(encoding='utf-8').replace('{{ARCHIVE_PREVIEWS}}', '<p>Old preview</p>')
                            .replace('</head>', '<meta name="test-layout" content="new">\n</head>'), encoding='utf-8')
        self.queue([self.post])
        self.run_at('2026-11-04T14:00:00+00:00')
        output = (self.public / 'index.html').read_text(encoding='utf-8')
        self.assertIn('test-layout', output)
        self.assertNotIn('Old preview', output)
        self.assertIn(self.post['slug'], output)


if __name__ == '__main__':
    unittest.main()
