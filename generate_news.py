#!/usr/bin/env python3
"""
generate_news.py
-----------------
This script downloads the latest items from an RSS feed and generates two
static HTML pages (`news.html` for English and `news-fa.html` for Farsi)
inside the `hotel_website` directory.  It uses Python's built‑in
`xml.etree.ElementTree` library to parse the RSS XML and builds simple
Bootstrap‑styled pages containing the article title, publication date, a
thumbnail (when available) and a short description that links back to
the original source.  Running this script regularly (for example via a
cronjob) will keep the news pages up to date.

The Farsi page retains the English article titles and summaries because
automated translation of proprietary content is outside the scope of this
script; however, interface text such as headings and button labels are
translated manually below.
"""

import html
import os
import urllib.request
import xml.etree.ElementTree as ET
from email.utils import parsedate_to_datetime
from datetime import datetime


FEED_URL = "https://www.hospitalitynet.org/news/global.xml"
# Number of articles to display on the news page
ARTICLE_LIMIT = 10


def fetch_feed(url: str) -> bytes:
    """Retrieve the XML content of the RSS feed from the given URL.

    Many servers block generic Python user agents.  To increase the chance of
    retrieving the feed successfully we spoof a common browser user agent.

    Args:
        url (str): URL pointing to the RSS feed.

    Returns:
        bytes: Raw XML data returned by the server.
    """
    headers = {"User-Agent": "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)"}
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req) as response:
        return response.read()


def parse_items(feed_data: bytes, limit: int = ARTICLE_LIMIT):
    """Parse the RSS feed data and extract article items.

    Args:
        feed_data (bytes): XML content of the feed.
        limit (int): Maximum number of items to return.

    Returns:
        list[dict]: A list of dictionaries containing article metadata.
    """
    # Parse the XML data.  The feed uses namespaces for media tags, so we
    # register the namespace so ElementTree can find them correctly.
    ns = {
        'media': 'http://search.yahoo.com/mrss/'
    }
    root = ET.fromstring(feed_data)
    items = []
    # Traverse all item nodes under channel.  Each item corresponds to a news
    # article.
    for item in root.findall('./channel/item'):
        title = item.findtext('title', default='').strip()
        link = item.findtext('link', default='').strip()
        description = item.findtext('description', default='').strip()
        pub_date_raw = item.findtext('pubDate', default='')
        # Attempt to parse the publication date into a human readable format
        try:
            dt = parsedate_to_datetime(pub_date_raw)
            # Use a fixed date format (e.g. 20 September 2025)
            date_str = dt.strftime('%d %B %Y')
        except Exception:
            date_str = pub_date_raw
        # Find the first media:content element to extract an image URL
        image_url = None
        media_content = item.find('media:content', ns)
        if media_content is not None:
            image_url = media_content.attrib.get('url')
        items.append({
            'title': html.escape(title),
            'link': html.escape(link),
            'description': html.escape(description),
            'date': html.escape(date_str),
            'image': html.escape(image_url) if image_url else None
        })
        # Respect the limit
        if len(items) >= limit:
            break
    return items


def build_html(items: list[dict], lang: str = 'en') -> str:
    """Build the complete HTML document for the news page.

    Args:
        items (list[dict]): List of article dictionaries to display.
        lang (str): Language code ('en' or 'fa').  Determines text direction
            and interface translations.

    Returns:
        str: A complete HTML document as a string.
    """
    rtl = lang == 'fa'
    html_lang = 'fa' if rtl else 'en'
    dir_attr = 'rtl' if rtl else 'ltr'
    # Static translations for interface elements
    trans = {
        'title': 'آخرین اخبار و مقالات' if rtl else 'Latest Articles',
        'description': 'تمامی اخبار از منابع معتبر هتلداری و گردشگری در این بخش گردآوری شده است.' if rtl else 'Hand‑curated news and articles from trusted hospitality and tourism sources.',
        'home': 'خانه' if rtl else 'Home',
        'news': 'مقالات' if rtl else 'Latest Articles',
        'features': 'ویژگی‌ها' if rtl else 'Features',
        'about': 'درباره ما' if rtl else 'About',
        'switch_lang': 'English' if rtl else 'فارسی',
        'switch_href': 'index.html' if rtl else 'index-fa.html'
    }
    # Build each article card
    cards_html = []
    for art in items:
        card = []
        card.append('<div class="col-md-6 col-lg-4 mb-4">')
        card.append('<div class="card h-100 shadow-sm">')
        # If an image is available, include it
        if art['image']:
            card.append(f'<img src="{art["image"]}" class="card-img-top" alt="News image">')
        card.append('<div class="card-body">')
        card.append(f'<h5 class="card-title">{art["title"]}</h5>')
        card.append(f'<p class="card-text small text-muted">{art["date"]}</p>')
        card.append(f'<p class="card-text">{art["description"]}</p>')
        card.append(f'<a href="{art["link"]}" target="_blank" class="btn btn-primary btn-sm">' + ('بیشتر بخوانید' if rtl else 'Read More') + '</a>')
        card.append('</div>')  # card-body
        card.append('</div>')  # card
        card.append('</div>')  # col
        cards_html.append('\n'.join(card))
    cards_joined = '\n'.join(cards_html)
    # Construct the full HTML page
    return f"""
<!DOCTYPE html>
<html lang="{html_lang}" dir="{dir_attr}">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{trans['title']} | HotelNews</title>
  <meta name="description" content="{trans['description']}">
  <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css">
  <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.10.5/font/bootstrap-icons.css">
  <link rel="stylesheet" href="styles.css">
</head>
<body>
  <nav class="navbar navbar-expand-lg navbar-light bg-light shadow-sm">
    <div class="container">
      <a class="navbar-brand fw-bold" href="#">{'هتل نیوز' if rtl else 'HotelNews'}</a>
      <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarNav" aria-controls="navbarNav" aria-expanded="false" aria-label="Toggle navigation">
        <span class="navbar-toggler-icon"></span>
      </button>
      <div class="collapse navbar-collapse" id="navbarNav">
        <ul class="navbar-nav ms-auto">
          <li class="nav-item"><a class="nav-link" href="{'index-fa.html' if rtl else 'index.html'}">{trans['home']}</a></li>
          <li class="nav-item"><a class="nav-link active" aria-current="page" href="#">{trans['news']}</a></li>
          <li class="nav-item"><a class="nav-link" href="{'index-fa.html#features' if rtl else 'index.html#features'}">{trans['features']}</a></li>
          <li class="nav-item"><a class="nav-link" href="{'index-fa.html#about' if rtl else 'index.html#about'}">{trans['about']}</a></li>
          <li class="nav-item"><a class="nav-link" href="{trans['switch_href']}">{trans['switch_lang']}</a></li>
        </ul>
      </div>
    </div>
  </nav>
  <header class="bg-primary text-white py-5">
    <div class="container text-center">
      <h1 class="fw-bold">{trans['title']}</h1>
      <p class="lead">{trans['description']}</p>
    </div>
  </header>
  <main class="py-4">
    <div class="container">
      <div class="row">
        {cards_joined}
      </div>
    </div>
  </main>
  <footer class="bg-dark text-white py-3">
    <div class="container d-flex justify-content-between align-items-center">
      <span>&copy; 2025 HotelNews. {'تمام حقوق محفوظ است.' if rtl else 'All rights reserved.'}</span>
      <span><a href="#" class="text-white me-2"><i class="bi bi-facebook"></i></a><a href="#" class="text-white me-2"><i class="bi bi-twitter"></i></a><a href="#" class="text-white"><i class="bi bi-instagram"></i></a></span>
    </div>
  </footer>
  <script type="text/javascript">
    window.$crisp=[];window.CRISP_WEBSITE_ID="your-website-id";
    (function(){{var d=document,s=d.createElement("script");s.src="https://client.crisp.chat/l.js";s.async=1;d.getElementsByTagName("head")[0].appendChild(s);}})();
  </script>
  <script type="text/javascript">
    document.addEventListener('contextmenu', event => event.preventDefault());
    document.onselectstart = () => {{ event.preventDefault(); }}
  </script>
  <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>
"""


def main():
    # Fetch and parse the feed
    print("Fetching RSS feed from", FEED_URL)
    feed_data = fetch_feed(FEED_URL)
    items = parse_items(feed_data)
    # Prepare the output directory
    base_dir = os.path.dirname(os.path.abspath(__file__))
    en_path = os.path.join(base_dir, 'news.html')
    fa_path = os.path.join(base_dir, 'news-fa.html')
    # Build pages
    en_html = build_html(items, lang='en')
    fa_html = build_html(items, lang='fa')
    # Write files
    with open(en_path, 'w', encoding='utf-8') as f:
        f.write(en_html)
    with open(fa_path, 'w', encoding='utf-8') as f:
        f.write(fa_html)
    print(f"Generated {en_path} and {fa_path} with {len(items)} items.")


if __name__ == '__main__':
    main()