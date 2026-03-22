import requests
from datetime import datetime
from email.utils import format_datetime
from xml.sax.saxutils import escape

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
        data = res.json()

        if not isinstance(data, list):
            print("Resposta inesperada:", data)
            return []

    except Exception as e:
        print("Erro na requisição:", e)
        return []

    posts = []

    for item in data:
        try:
            title = item.get("title", {}).get("rendered", "").strip()
            link = item.get("link", "")
            date_str = item.get("date_gmt") or item.get("date")

            dt = datetime.utcnow()
            if date_str:
                try:
                    dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
                except:
                    pass

            description = item.get("excerpt", {}).get("rendered", "")

            image_url = None
            if "_embedded" in item:
                media = item["_embedded"].get("wp:featuredmedia")
                if media and isinstance(media, list):
                    image_url = media[0].get("source_url")

            posts.append({
                "title": title,
                "link": link,
                "pubDate": format_datetime(dt),
                "description": description,
                "image": image_url
            })

        except Exception as e:
            print("Erro ao processar post:", e)
            continue

    return posts

def generate_rss(posts):
    items = ""

    for p in posts:
        description = p["description"] or ""

        if p["image"]:
            description = f'<img src="{p["image"]}"/><br/>' + description

        items += f"""
        <item>
            <title>{escape(p['title'])}</title>
            <link>{p['link']}</link>
            <guid>{p['link']}</guid>
            <pubDate>{p['pubDate']}</pubDate>
            <description><![CDATA[{description}]]></description>
        </item>
        """

    rss = f"""<?xml version="1.0" encoding="UTF-8"?>
    <rss version="2.0" xmlns:media="http://search.yahoo.com/mrss/">
      <channel>
        <title>Curitiba Cult</title>
        <link>{URL}</link>
        <description>Últimos posts do Curitiba Cult</description>
        <language>pt-BR</language>
        <lastBuildDate>{format_datetime(datetime.utcnow())}</lastBuildDate>
        {items}
      </channel>
    </rss>
    """

    return rss


if __name__ == "__main__":
    posts = fetch_posts()

    if not posts:
        print("Nenhum post encontrado, mas continuando...")

    rss = generate_rss(posts)

    with open("feed.xml", "w", encoding="utf-8") as f:
        f.write(rss)

    print(f"Feed gerado com {len(posts)} posts")
