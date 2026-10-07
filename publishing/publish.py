#!/usr/bin/env python3
"""Publish approved, due archive entries. Run from CLI or cPanel Cron Jobs."""
import argparse
import html
import json
import os
from pathlib import Path
import re
import sys
import tempfile
from datetime import datetime, timezone
from email.utils import format_datetime
from xml.etree import ElementTree as ET

HERE = Path(__file__).resolve().parent
SITE_URL = 'https://selenamonroe.com'
NS = 'http://www.sitemaps.org/schemas/sitemap/0.9'
ET.register_namespace('', NS)


def load(path):
    return json.loads(path.read_text(encoding='utf-8'))


def instant(value):
    if not isinstance(value, str) or not re.fullmatch(
            r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:Z|[+-]\d{2}:\d{2})', value):
        raise ValueError('Publication times must include an explicit timezone offset')
    normalized = value[:-1] + '+0000' if value.endswith('Z') else value[:-3] + value[-2:]
    return datetime.strptime(normalized, '%Y-%m-%dT%H:%M:%S%z')


def validate(post):
    for key in ('slug', 'title', 'dek', 'date', 'displayDate', 'category',
                'readTime', 'description', 'excerpt'):
        if not isinstance(post.get(key), str) or not post[key].strip():
            raise ValueError('Missing post field: ' + key)
    if not re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*', post['slug']):
        raise ValueError('Invalid article slug')
    datetime.strptime(post['date'], '%Y-%m-%d')
    if 'publish_at' in post:
        if instant(post['publish_at']).strftime('%Y-%m-%d') != post['date']:
            raise ValueError('Publication date and article date disagree')


def esc(value):
    return html.escape(str(value), quote=True)


def atomic_write(path, text, public=False):
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and path.read_text(encoding='utf-8') == text:
        return
    fd, temp = tempfile.mkstemp(prefix='.publish-', dir=str(path.parent))
    try:
        with os.fdopen(fd, 'w', encoding='utf-8', newline='\n') as handle:
            handle.write(text)
        os.chmod(temp, 0o644 if public else 0o600)
        os.replace(temp, path)
    finally:
        if os.path.exists(temp):
            os.unlink(temp)


def fill(template, values):
    for key, value in values.items():
        token = '{{' + key + '}}'
        if token not in template:
            raise ValueError('Template missing marker ' + token)
        template = template.replace(token, value)
    return template


def listing(post, preview=False):
    if preview:
        return ('<a class="archive-preview-card" href="archive/{slug}/">'
                '<div><time datetime="{date}">{displayDate}<br>{category}</time>'
                '<h3>{title}</h3></div><p>{excerpt}</p></a>').format(
                    **{key: esc(value) for key, value in post.items()})
    return ('<a class="dispatch-card" href="archive/{slug}/">'
            '<time datetime="{date}">{displayDate}<br>{category}</time>'
            '<div><h2>{title}</h2><p>{excerpt}</p></div>'
            '<span class="arrow" aria-hidden="true">-&gt;</span></a>').format(
                **{key: esc(value) for key, value in post.items()})


def list_template(template, marker, pattern, content):
    if '{{' + marker + '}}' in template:
        return fill(template, {marker: content})
    updated, count = re.subn(pattern, lambda match: match[1] + '\n' + content + '\n' + match[2], template)
    if count != 1:
        raise ValueError('Could not locate exactly one archive listing in template')
    return updated


def article(post, template):
    url = SITE_URL + '/archive/' + post['slug'] + '/'
    schema = {
        '@context': 'https://schema.org', '@type': 'BlogPosting',
        'headline': post['title'], 'description': post['description'],
        'datePublished': post['publish_at'], 'dateModified': post['publish_at'],
        'mainEntityOfPage': url, 'url': url, 'inLanguage': 'en-US',
        'image': SITE_URL + '/Website_Banner_web.jpg',
        'author': {'@type': 'Person', 'name': 'Selena Monroe', 'url': SITE_URL},
        'isPartOf': {'@type': 'Blog', 'name': 'Selena Monroe Archive',
                     'url': SITE_URL + '/archive.html'},
        'keywords': post.get('keywords', [])
    }
    return fill(template, {
        'TITLE': esc(post['title']), 'DESCRIPTION': esc(post['description']),
        'URL': esc(url), 'SCHEMA': json.dumps(schema).replace('<', '\\u003c'),
        'CATEGORY': esc(post['category']), 'DEK': esc(post['dek']),
        'DATE': esc(post['date']), 'DISPLAY_DATE': esc(post['displayDate']),
        'READ_TIME': esc(post['readTime']), 'BODY': post['body_html'],
        'NOTE': post.get('note_html', 'Spoiler-light companion worldbuilding. '
                         '<a href="../../monstrous-beloved.html">The Monstrous Beloved</a> '
                         '&middot; <a href="../../content-notes.html">Content Notes</a>')
    })


def outputs(source, public, base, published):
    posts = base + [{k: v for k, v in p.items()
                     if k not in ('body_html', 'note_html', 'approved')}
                    for p in published.values()]
    posts.sort(key=lambda p: (p['date'], p['slug']), reverse=True)
    templates = source / 'templates'
    files = {}
    if published:
        template = (templates / 'article.html').read_text(encoding='utf-8')
        for post in published.values():
            page = article(post, template)
            files['archive/' + post['slug'] + '/index.html'] = page
            files['archive/' + post['slug'] + '.html'] = page.replace('../../', '../')
    files['posts.json'] = json.dumps({'posts': posts}, indent=2, ensure_ascii=False) + '\n'
    files['index.html'] = list_template(
        (templates / 'index.html').read_text(encoding='utf-8'), 'ARCHIVE_PREVIEWS',
        r'(<div class="archive-preview-grid">)[\s\S]*?(</div>\s*</section>)',
        '\n'.join(listing(p, True) for p in posts[:3]))
    files['archive.html'] = list_template(
        (templates / 'archive.html').read_text(encoding='utf-8'), 'ARCHIVE_LIST',
        r'(<section class="dispatch-list" aria-label="Archive entries">)[\s\S]*?(</section>)',
        '\n'.join(listing(p) for p in posts))
    feed = ET.Element('rss', {'version': '2.0'})
    channel = ET.SubElement(feed, 'channel')
    for tag, value in [('title', 'Selena Monroe Archive'),
                       ('link', SITE_URL + '/archive.html'),
                       ('description', 'Lore, worldbuilding, creature notes, and book-adjacent essays from Selena Monroe.'),
                       ('language', 'en-us')]:
        ET.SubElement(channel, tag).text = value
    for post in posts:
        item = ET.SubElement(channel, 'item')
        url = SITE_URL + '/archive/' + post['slug'] + '/'
        date = instant(post.get('publish_at', post['date'] + 'T16:00:00+00:00'))
        for tag, value in [('title', post['title']), ('link', url), ('guid', url),
                           ('pubDate', format_datetime(date.astimezone(timezone.utc), usegmt=True)),
                           ('description', post['excerpt'])]:
            ET.SubElement(item, tag).text = value
    files['archive-feed.xml'] = '<?xml version="1.0" encoding="UTF-8"?>\n' + ET.tostring(feed, encoding='unicode') + '\n'
    sitemap = ET.parse(templates / 'sitemap.xml').getroot()
    for node in list(sitemap):
        loc = node.find('{' + NS + '}loc')
        if loc is not None and loc.text.startswith(SITE_URL + '/archive/'):
            sitemap.remove(node)
    for post in posts:
        node = ET.SubElement(sitemap, '{' + NS + '}url')
        for tag, value in [('loc', SITE_URL + '/archive/' + post['slug'] + '/'),
                           ('lastmod', post['date']), ('changefreq', 'yearly'), ('priority', '0.7')]:
            ET.SubElement(node, '{' + NS + '}' + tag).text = value
    files['sitemap.xml'] = '<?xml version="1.0" encoding="UTF-8"?>\n' + ET.tostring(sitemap, encoding='unicode') + '\n'
    return files


def publish(source, public, state, now, dry_run=False):
    # Persistent state survives Git deployments; source templates track current site edits.
    base = load(source / 'base-posts.json')['posts']
    queue = load(source / 'queue.json')['posts']
    seen = set()
    for post in base + queue:
        validate(post)
        if post['slug'] in seen:
            raise ValueError('Duplicate post slug: ' + post['slug'])
        seen.add(post['slug'])
    published = load(state / 'published.json') if (state / 'published.json').exists() else {}
    for slug, post in published.items():
        validate(post)
        if slug != post['slug'] or slug in {p['slug'] for p in base}:
            raise ValueError('Published article conflicts with base: ' + slug)
    changed = []
    for post in queue:
        if post.get('approved') is not True:
            continue
        if instant(post['publish_at']) > now:
            continue
        if not post.get('body_html', '').strip():
            raise ValueError('Approved article has no body: ' + post['slug'])
        if published.get(post['slug']) != post:
            changed.append(post['slug'])
        published[post['slug']] = post
    files = outputs(source, public, base, published)
    if dry_run:
        print(json.dumps({'due': changed, 'published': list(published), 'outputs': list(files)}, indent=2))
        return files
    for name, text in files.items():
        atomic_write(public / name, text, public=True)
    atomic_write(state / 'published.json', json.dumps(published, indent=2, ensure_ascii=False) + '\n')
    if changed:
        print('Published: ' + ', '.join(changed))
    return files


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--public-root', type=Path, default=HERE.parent / 'public_html')
    parser.add_argument('--state-root', type=Path, default=HERE.parent / 'selena-publisher-state')
    parser.add_argument('--dry-run', action='store_true')
    args = parser.parse_args()
    public = args.public_root.resolve()
    state = args.state_root.resolve()
    if not (public / 'index.html').is_file():
        raise ValueError('Public root must contain the existing website')
    if public == HERE or public in HERE.parents or public == state or public in state.parents:
        raise ValueError('Publisher source and state must be outside the public website')
    if args.dry_run:
        publish(HERE, public, state, datetime.now(timezone.utc), True)
        return
    import fcntl
    state.mkdir(parents=True, exist_ok=True, mode=0o700)
    with (state / 'publisher.lock').open('a') as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            return
        publish(HERE, public, state, datetime.now(timezone.utc))


if __name__ == '__main__':
    try:
        main()
    except Exception as exc:
        print('Archive publisher failed: ' + str(exc), file=sys.stderr)
        sys.exit(1)
