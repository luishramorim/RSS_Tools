import requests
import os
from datetime import datetime, UTC
from email.utils import format_datetime
from xml.sax.saxutils import escape
import html
import time

SITES = [
    {
        "name": "Curitiba Cult",
        "url": "https://curitibacult.com.br",
        "description": "Últimos posts do Curitiba Cult",
        "output_dir": "Curitiba Cult RSS"
    },
    {
        "name": "O Que Fazer Curitiba",
        "url": "https://oquefazercuritiba.com.br",
        "description": "Últimas dicas e notícias de O Que Fazer Curitiba",
        "output_dir": "O Que Fazer Curitiba RSS"
    }
]

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}

def fetch_posts(api_url):
    try:
        res = requests.get(api_url, headers=HEADERS, params={
            "per_page": 20,
            "_embed": "true"
        }, timeout=15)

        print(f"[{api_url}] Status: {res.status_code}")
        res.raise_for_status()

        try:
            data = res.json()
        except Exception as e:
            print(f"[{api_url}] Erro ao fazer parse do JSON: {e}")
            return []

        if not isinstance(data, list):
            print(f"[{api_url}] Resposta inesperada: não é uma lista")
            return []

    except Exception as e:
        print(f"[{api_url}] Erro na requisição: {e}")
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
            print(f"[{api_url}] Erro ao processar post: {e}")
            continue

    return posts

def generate_rss(posts, site_config):
    items = ""

    for p in posts:
        description = p.get("description", "") or ""
        content = p.get("content", "") or ""

        # Usar o conteúdo completo para garantir que feeds ignorando <content:encoded> exibam a matéria inteira
        if content:
            description = content

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
        <title>{site_config["name"]}</title>
        <link>{site_config["url"]}</link>
        <description>{site_config["description"]}</description>
        <language>pt-BR</language>
        <lastBuildDate>{format_datetime(datetime.now(UTC))}</lastBuildDate>
        {items}
      </channel>
    </rss>
    """

    return rss


if __name__ == "__main__":
    script_dir = os.path.dirname(os.path.abspath(__file__))

    for site in SITES:
        print(f"\\n--- Extraindo posts para {site['name']} ---")
        api_url = f"{site['url']}/wp-json/wp/v2/posts"
        
        posts = fetch_posts(api_url)

        if len(posts) == 0:
            print(f"⚠️ AVISO: Nenhum post encontrado na API. Ignorando a geração para {site['name']} para não sobrescrever o feed atual do GitHub com um arquivo vazio.")
            continue

        rss = generate_rss(posts, site)

        # Ensure directory exists just in case
        output_dir_path = os.path.join(script_dir, site['output_dir'])
        if not os.path.exists(output_dir_path):
            os.makedirs(output_dir_path)

        feed_path = os.path.join(output_dir_path, "feed.xml")
        with open(feed_path, "w", encoding="utf-8") as f:
            f.write(rss)

        print(f"✅ Feed atualizado para {site['name']} com {len(posts)} posts! Salvo em: {site['output_dir']}/feed.xml")
        
        # Prevenção simples de block caso os sites estivessem no mesmo servidor
        time.sleep(1)
        
    print("\\n🚀 Todas as fontes processadas com sucesso.")
