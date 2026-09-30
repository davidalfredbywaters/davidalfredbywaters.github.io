#!/usr/bin/env python3
"""Build the website.

    python3 build.py            -> writes the finished site into  public/
    python3 build.py --serve    -> builds, then previews it at http://localhost:8000
    python3 build.py --preview  -> like --serve, but also shows scheduled and draft
                                   posts (only on your Mac; nothing is published)

Posts live in content/blog/, pages in content/pages/. Each is a Markdown file
with a short header (title, date, url). Pictures go in static/images/,
downloadable files in static/s/. Posts dated in the future stay hidden until
that date arrives (the site is rebuilt automatically every day).
"""
import datetime as dt, email.utils, html, math, os, re, shutil, sys
import markdown, yaml
from jinja2 import Environment, FileSystemLoader

ROOT = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(ROOT, 'public')
PREVIEW = '--preview' in sys.argv          # show scheduled + draft posts locally
NOW = dt.datetime.now(dt.timezone.utc).replace(tzinfo=None)
if PREVIEW:
    NOW = dt.datetime.max

cfg = yaml.safe_load(open(os.path.join(ROOT, 'config.yaml'), encoding='utf-8'))
env = Environment(loader=FileSystemLoader(os.path.join(ROOT, 'templates')), autoescape=False)
env.globals.update(site=cfg)

MD_EXT = ['extra', 'sane_lists']

FIGURE = re.compile(r'<p>\s*<img alt="([^"]*)" src="([^"]+)" title="([^"]*)"\s*/?>\s*</p>')

def render_markdown(text):
    body = markdown.markdown(text, extensions=MD_EXT, output_format='html')
    # An image written as  ![alt](picture.jpg "Caption")  becomes a captioned figure.
    body = FIGURE.sub(lambda m: f'<figure><img alt="{m.group(1)}" src="{m.group(2)}" loading="lazy">'
                                f'<figcaption>{m.group(3)}</figcaption></figure>', body)
    body = re.sub(r'<img (?![^>]*loading=)', '<img loading="lazy" ', body)
    button = (f'<p class="donate"><a class="button" href="{html.escape(cfg["donate_url"])}">Donate</a></p>'
              if cfg.get('donate_url') else '')
    body = re.sub(r'<p>\s*\{\{ donate \}\}\s*</p>', button, body).replace('{{ donate }}', button)
    if '{{ subscribe_form }}' in body:
        form = env.get_template('_subscribe_form.html').render()
        body = re.sub(r'<p>\s*\{\{ subscribe_form \}\}\s*</p>', form, body)
    return body

def load(folder, kind):
    items = []
    path = os.path.join(ROOT, 'content', folder)
    for name in sorted(os.listdir(path)):
        if not name.endswith('.md'):
            continue
        raw = open(os.path.join(path, name), encoding='utf-8').read()
        m = re.match(r'^---\s*\n(.*?)\n---\s*\n?(.*)$', raw, re.S)
        if not m:
            print(f'  skipped {folder}/{name}: no header'); continue
        meta = yaml.safe_load(m.group(1)) or {}
        if meta.get('draft') and not PREVIEW:
            continue
        date = meta.get('date')
        if isinstance(date, str):
            date = dt.datetime.fromisoformat(date.strip().replace('Z', '+00:00'))
        elif isinstance(date, dt.date) and not isinstance(date, dt.datetime):
            date = dt.datetime(date.year, date.month, date.day)
        if isinstance(date, dt.datetime) and date.tzinfo:
            date = date.astimezone(dt.timezone.utc).replace(tzinfo=None)
        if kind == 'post':
            if date is None:
                print(f'  skipped {folder}/{name}: no date'); continue
            if date > NOW:
                continue                      # scheduled for later
        url = meta.get('url') or (f'/blog/{date.year}/{date.month}/{date.day}/{name[:-3]}' if kind == 'post'
                                  else '/' + name[:-3])
        url = '/' + url.strip('/')
        items.append(dict(title=str(meta.get('title', name[:-3])), date=date, url=url, kind=kind,
                          categories=meta.get('categories') or [], description=meta.get('description'),
                          content=render_markdown(m.group(2)), source=f'{folder}/{name}'))
    return items

def write(url, text):
    path = os.path.join(OUT, url.strip('/'), 'index.html') if not url.endswith(('.xml', '.html', '.txt')) \
        else os.path.join(OUT, url.lstrip('/'))
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as fh:
        fh.write(text)

def fmt_date(d):
    return f'{d:%B} {d.day}, {d.year}'
env.filters['nice_date'] = fmt_date

def listing(posts, base, heading=None):
    per = cfg.get('posts_per_page', 20)
    pages = max(1, math.ceil(len(posts) / per))
    for n in range(pages):
        url = base if n == 0 else f'{base.rstrip("/")}/page/{n + 1}'
        newer = None if n == 0 else (base if n == 1 else f'{base.rstrip("/")}/page/{n}')
        older = f'{base.rstrip("/")}/page/{n + 2}' if n + 1 < pages else None
        write(url, env.get_template('list.html').render(
            posts=posts[n * per:(n + 1) * per], newer=newer, older=older, heading=heading,
            page_title=heading, url=url))

def main():
    if os.path.exists(OUT):
        shutil.rmtree(OUT)
    shutil.copytree(os.path.join(ROOT, 'static'), OUT)

    posts = sorted(load('blog', 'post'), key=lambda p: p['date'], reverse=True)
    pages = load('pages', 'page')

    for i, p in enumerate(posts):
        newer = posts[i - 1] if i > 0 else None
        older = posts[i + 1] if i + 1 < len(posts) else None
        write(p['url'], env.get_template('post.html').render(post=p, newer=newer, older=older,
                                                             page_title=p['title'], url=p['url']))
    for p in pages:
        write(p['url'], env.get_template('page.html').render(page=p, page_title=p['title'], url=p['url']))

    listing(posts, '/')
    listing(posts, '/blog')
    cats = sorted({c for p in posts for c in p['categories']})
    for c in cats:
        listing([p for p in posts if c in p['categories']], f'/blog/category/{c}', heading=c)

    # RSS feed (newest 20 posts) and sitemap
    feed = posts[:20]
    for p in feed:
        p['rfc822'] = email.utils.format_datetime(p['date'].replace(tzinfo=dt.timezone.utc))
    rss = env.get_template('rss.xml').render(posts=feed)
    write('/blog/rss.xml', rss)
    write('/rss.xml', rss)
    urls = ['/'] + [p['url'] for p in posts] + [p['url'] for p in pages]
    write('/sitemap.xml', env.get_template('sitemap.xml').render(urls=urls))
    write('/robots.txt', f'User-agent: *\nAllow: /\nSitemap: {cfg["base_url"]}/sitemap.xml\n')
    write('/404.html', env.get_template('page.html').render(
        page=dict(title='Page Not Found', content='<p>Sorry, that page doesn’t exist. '
                  '<a href="/">Return to the blog.</a></p>'), page_title='Page Not Found', url='/404'))

    domain = re.sub(r'^https?://', '', cfg['base_url']).strip('/')
    write('/CNAME.txt', domain)
    os.rename(os.path.join(OUT, 'CNAME.txt'), os.path.join(OUT, 'CNAME'))
    open(os.path.join(OUT, '.nojekyll'), 'w').close()

    print(f'Built {len(posts)} posts and {len(pages)} pages into public/')

if __name__ == '__main__':
    main()
    if '--serve' in sys.argv or PREVIEW:
        import http.server, functools
        handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=OUT)
        print('Preview at http://localhost:8000  (press Control-C to stop)')
        http.server.ThreadingHTTPServer(('127.0.0.1', 8000), handler).serve_forever()
