import time
import os
import sqlite3
import requests
from bs4 import BeautifulSoup

file_path = "github_page.html"

if os.path.exists(file_path):
    print("ローカルに保存されたHTMLファイルを使用して解析します。")
    with open(file_path, "r", encoding="utf-8") as f:
        html_content = f.read()
    status_code = 200
else:
    print("サーバーにリクエストを送信します...")
    url = "https://github.com/orgs/google/repositories"
    time.sleep(3)
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    res = requests.get(url, headers=headers)
    status_code = res.status_code
    if status_code == 200:
        html_content = res.text
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(html_content)

if status_code == 200:
    soup = BeautifulSoup(html_content, "html.parser")
    
    links = soup.select('a[href^="/google/"]')
    
    repo_data_list = []
    seen_names = set()
    
    for a in links:
        href = a.get("href")
        parts = href.split("/")
        if len(parts) < 3 or parts[2] == "":
            continue
            
        repo_name = parts[2]
        
        if repo_name in ("repositories", "site", "about") or repo_name in seen_names:
            continue
            
        seen_names.add(repo_name)
        
        card = a.find_parent(["li", "div", "article"])
        
        parent_candidate = a.parent
        for _ in range(8):
            if parent_candidate:
                if parent_candidate.select_one('a[href$="/stargazers"]'):
                    card = parent_candidate
                    break
                parent_candidate = parent_candidate.parent
        
        language = "なし"
        if card:
            lang_tag = card.select_one('[itemprop="programmingLanguage"]')
            if lang_tag and lang_tag.text.strip():
                language = lang_tag.text.strip()
            else:
                spans = card.select('span')
                for s in spans:
                    text = s.text.strip()
                    if text and not text.startswith("Updated") and not text.startswith("Star") and not any(char.isdigit() for char in text) and len(text) < 20:
                        if text not in (repo_name, "Public", "Private", "Fork", "Sponsor"):
                            language = text
                            break
        
        star_tag = card.select_one('a[href$="/stargazers"]') if card else None
        stars = star_tag.text.strip() if star_tag else "0"
        
        repo_data_list.append((repo_name, language, stars))
        
    print(f"取得できたリポジトリ数: {len(repo_data_list)}")

    conn = sqlite3.connect("github_repos.db")
    cursor = conn.cursor()

    cursor.execute("DROP TABLE IF EXISTS repositories")
    cursor.execute("""
        CREATE TABLE repositories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            language TEXT,
            stars TEXT
        )
    """)

    cursor.executemany("""
        INSERT INTO repositories (name, language, stars)
        VALUES (?, ?, ?)
    """, repo_data_list)

    conn.commit()

    print("\n--- SQLiteデータベースからの全件抽出結果 ---")
    cursor.execute("SELECT * FROM repositories")
    rows = cursor.fetchall()

    for row in rows:
        print(f"ID: {row[0]} | 名前: {row[1]} | 言語: {row[2]} | スター数: {row[3]}")

    conn.close()

else:
    print("アクセス失敗:", status_code)