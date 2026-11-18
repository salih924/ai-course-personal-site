"""Build Salih's static pages from the three news feeds or their saved snapshot."""
import argparse
import json
import os
import shutil
import sys
import textwrap
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from html import escape
from html.parser import HTMLParser
from http.client import HTTPException
from pathlib import Path
from string import Template
from tempfile import NamedTemporaryFile
from urllib.error import URLError
from urllib.parse import urlsplit
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
SNAPSHOT = ROOT / "data/news.json"
STORY_LIMIT = 6


class PlainText(HTMLParser):
    def __init__(self):
        super().__init__()
        self.fragments = []

    def handle_data(self, data):
        self.fragments.append(data)

    def handle_starttag(self, tag, attrs):
        if tag in {"p", "div", "br", "li"}:
            self.fragments.append(" ")

    def handle_endtag(self, tag):
        if tag in {"p", "div", "li"}:
            self.fragments.append(" ")


def plain_text(raw):
    parser = PlainText()
    parser.feed(raw or "")
    parser.close()
    return " ".join("".join(parser.fragments).split())


def fetch_stories(url):
    request = Request(url, headers={"User-Agent": "SalihBisharaNews/1.0 (student RSS reader)"})
    with urlopen(request, timeout=18) as response:
        root = ET.fromstring(response.read(4_000_001))
    by_link = {}
    for item in root.findall("./channel/item"):
        title = plain_text(item.findtext("title"))
        link = (item.findtext("link") or "").strip()
        if not title or urlsplit(link).scheme not in {"http", "https"} or not urlsplit(link).hostname:
            continue
        try:
            date = parsedate_to_datetime(item.findtext("pubDate") or "")
            if date.tzinfo is None:
                continue
        except (ValueError, TypeError, OverflowError):
            continue
        summary = textwrap.shorten(plain_text(item.findtext("description")), width=160, placeholder="…")
        story = {"title": title, "url": link, "date": date.astimezone(timezone.utc).isoformat(), "summary": summary}
        if link not in by_link or by_link[link]["date"] < story["date"]:
            by_link[link] = story
    if not by_link:
        raise ValueError("The feed contained no dated article links")
    return sorted(by_link.values(), key=lambda story: story["date"], reverse=True)[:STORY_LIMIT]


def refresh_topics(topics, saved):
    result = dict(saved)
    for topic in topics:
        slug = topic["slug"]
        try:
            stories = fetch_stories(topic["feed"])
        except (OSError, URLError, ET.ParseError, ValueError, HTTPException) as error:
            if not saved.get(slug, {}).get("stories"):
                raise RuntimeError(f"{slug}: no saved stories available") from error
            print(f"{slug}: keeping last successful refresh ({error})", file=sys.stderr)
            continue
        result[slug] = {"updated": datetime.now(timezone.utc).date().isoformat(), "stories": stories}
        print(f"{topic['name']}: {len(stories)} stories")
    return result


def write_snapshot(data):
    with NamedTemporaryFile("w", dir=SNAPSHOT.parent, delete=False, encoding="utf-8") as handle:
        json.dump(data, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
    os.replace(handle.name, SNAPSHOT)


def template(filename, **values):
    source = (ROOT / "templates" / f"{filename}.html").read_text(encoding="utf-8")
    return Template(source).substitute(values)


def date_label(iso_date):
    date = datetime.fromisoformat(iso_date)
    return f"{date.day} {date:%b %Y}"


def metadata(topic, story):
    return (f'<div class="meta"><span>{escape(topic["publisher"])}</span>'
            f'<time datetime="{escape(story["date"])}">{date_label(story["date"])}</time></div>')


def home_card(topic, record):
    story = record["stories"][0]
    slug, name = escape(topic["slug"]), escape(topic["name"])
    return f"""
    <article class="lead-card {slug}">
      <a class="cover" href="{slug}.html" aria-label="Browse {name} news">
        <img src="assets/{slug}.jpg" alt="" loading="lazy">
        <span class="tag">{name}</span>
      </a>
      <div class="lead-content">
        {metadata(topic, story)}
        <h3><a href="{escape(story['url'])}">{escape(story['title'])}</a></h3>
        <a class="topic-link" href="{slug}.html">All {name.lower()} news <span aria-hidden="true">→</span></a>
      </div>
    </article>"""


def story_card(topic, story):
    summary = f'<p>{escape(story["summary"])}</p>' if story["summary"] else ""
    return f"""
    <article class="story">
      {metadata(topic, story)}
      <h3><a href="{escape(story['url'])}">{escape(story['title'])}</a></h3>
      {summary}
      <span class="read" aria-hidden="true">Read story ↗</span>
    </article>"""


def build(site, news, output):
    output.mkdir(parents=True, exist_ok=True)
    shutil.copytree(ROOT / "assets", output / "assets", dirs_exist_ok=True)
    topics = site["topics"]
    pages = [("index", "Home")] + [(t["slug"], t["name"]) for t in topics]

    def write_page(slug, title, description, body):
        nav = []
        for path, label in pages:
            current = ' aria-current="page"' if path == slug else ""
            nav.append(f'<a href="{escape(path)}.html"{current}>{escape(label)}</a>')
        html = template("page", nav="\n".join(nav), body=body, title=escape(title),
                        description=escape(description), site_title=escape(site["title"]),
                        github=escape(site["github"]))
        (output / f"{slug}.html").write_text(html, encoding="utf-8")

    home = template("home", intro=escape(site["introduction"]),
                    cards="".join(home_card(t, news[t["slug"]]) for t in topics))
    write_page("index", site["title"], site["introduction"], home)
    for topic in topics:
        slug = topic["slug"]
        record = news[slug]
        body = template("topic", slug=escape(slug), name=escape(topic["name"]),
                        publisher=escape(topic["publisher"]), topic_description=escape(topic["description"]),
                        updated=date_label(record["updated"]),
                        cards="".join(story_card(topic, story) for story in record["stories"]))
        write_page(slug, f"{topic['name']} | {site['title']}", topic["description"], body)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--offline", action="store_true", help="Build using the saved news only")
    args = parser.parse_args()
    site = json.loads((ROOT / "data/site.json").read_text(encoding="utf-8"))
    news = json.loads(SNAPSHOT.read_text(encoding="utf-8")) if SNAPSHOT.exists() else {}
    if not args.offline:
        news = refresh_topics(site["topics"], news)
    build(site, news, ROOT / "dist")
    if not args.offline:
        write_snapshot(news)
    print("Built dist/index.html and three topic pages")


if __name__ == "__main__":
    main()
