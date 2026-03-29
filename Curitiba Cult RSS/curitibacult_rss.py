import requests
from datetime import datetime, UTC
from email.utils import format_datetime
from xml.sax.saxutils import escape
import html

URL = "https://curitibacult.com.br"
WP_API = f"{URL}/wp-json/wp/v2/posts"

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}

def fetch_posts():
    try:
        res = requests.get(WP_API, headers=HEADERS, params={
            "per_page": 20,
            "_embed": "true"
        }, timeout=10)

        print("Status:", res.status_code)

        res.raise_for_status()
        try:
            data = res.json()
        except Exception as e:
            print("Erro ao fazer parse do JSON:", e)
            return []

        if not isinstance(data, list):
            print("Resposta inesperada:", data)
            return []

    except Exception as e:
        print("Erro na requisição:", e)
        return []

    posts = []

    for item in data:
        try:
            title = html.unescape(item.get("title", {}).get("rendered", "").strip())
            link = item.get("link", "")
            date_str = item.get("date_gmt") or item.get("date")

            dt = datetime.now(UTC)
            if isinstance(date_str, str):
                try:
                    dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
                except Exception as e:
                    print("Erro ao parsear data:", e)

            description = html.unescape(item.get("excerpt", {}).get("rendered", ""))
            content = html.unescape(item.get("content", {}).get("rendered", ""))

            image_url = None
            embedded = item.get("_embedded", {})
            media = embedded.get("wp:featuredmedia", [])
            if isinstance(media, list) and len(media) > 0:
                image_url = media[0].get("source_url")

            posts.append({
                "title": title,
                "link": link,
                "pubDate": format_datetime(dt),
                "description": description,
                "content": content,
                "image": image_url
            })

        except Exception as e:
            print("Erro ao processar post:", e)
            continue

    return posts

def generate_rss(posts):
    items = ""

    for p in posts:
        description = p.get("description", "") or ""
        content = p.get("content", "") or ""

        if p.get("image"):
            image_tag = f'<img src="{p["image"]}"/><br/>'
            description = image_tag + description
            content = image_tag + content

        items += f"""
        <item>
            <title>{escape(p['title'])}</title>
            <link>{p['link']}</link>
            <guid>{p['link']}</guid>
            <pubDate>{p['pubDate']}</pubDate>
            <description><![CDATA[{description}]]></description>
            <content:encoded><![CDATA[{content}]]></content:encoded>
        </item>
        """

    rss = f"""<?xml version="1.0" encoding="UTF-8"?>
    <rss version="2.0"
         xmlns:media="http://search.yahoo.com/mrss/"
         xmlns:content="http://purl.org/rss/1.0/modules/content/">
      <channel>
        <title>Curitiba Cult</title>
        <link>{URL}</link>
        <description>Últimos posts do Curitiba Cult</description>
        <language>pt-BR</language>
        <lastBuildDate>{format_datetime(datetime.now(UTC))}</lastBuildDate>
        {items}
      </channel>
    </rss>
    """

    return rss


if __name__ == "__main__":
    posts = fetch_posts()

    if not posts:
        print("Nenhum post encontrado — gerando feed vazio")

    rss = generate_rss(posts)

    with open("feed.xml", "w", encoding="utf-8") as f:
        f.write(rss)

    print(f"Feed gerado com {len(posts)} posts")
