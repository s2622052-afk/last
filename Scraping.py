import sqlite3
import time
from bs4 import BeautifulSoup
import requests

headers = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
        " (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )
}

repo_data_list = []
seen_names = set()
page = 1

print("Googleのリポジトリを全件スクレイピングします...")

while True:
  url = f"https://github.com/orgs/google/repositories?page={page}"
  time.sleep(5)  
  res = requests.get(url, headers=headers)

  if res.status_code != 200:
    print(f"ページ {page} の取得終了/失敗 (ステータスコード: {res.status_code})")
    break

  soup = BeautifulSoup(res.text, "html.parser")
  links = soup.select('a[href^="/google/"]')

  added_in_this_page = 0

  for a in links:
    href = a.get("href", "")
    parts = href.split("/")
    if len(parts) != 3 or parts[2] == "":
      continue

    repo_name = parts[2]
    if repo_name in ("repositories", "site", "about") or repo_name in seen_names:
      continue

    card = None
    parent_candidate = a.parent
    for _ in range(8):
      if parent_candidate:
        if parent_candidate.select_one('a[href$="/stargazers"]'):
          card = parent_candidate
          break
        parent_candidate = parent_candidate.parent

    if not card:
      continue
    seen_names.add(repo_name)
    added_in_this_page += 1

    language = "なし"
    lang_tag = card.select_one('[itemprop="programmingLanguage"]')
    if lang_tag and lang_tag.text.strip():
      language = lang_tag.text.strip()
    else:
      color_dot = card.select_one('span[style*="background-color"]')
      if color_dot and color_dot.parent:
        lang_text = color_dot.parent.get_text(strip=True)
        if lang_text:
          language = lang_text

    star_tag = card.select_one('a[href$="/stargazers"]')
    stars = star_tag.text.strip() if star_tag else "0"

    repo_data_list.append((repo_name, language, stars))

  print(f"ページ {page} 完了: {added_in_this_page}件取得（累計: {len(repo_data_list)}件）")
  if added_in_this_page == 0:
    break

  page += 1
print(f"\n合計取得リポジトリ数: {len(repo_data_list)}件")

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

cursor.executemany(
    """
    INSERT INTO repositories (name, language, stars)
    VALUES (?, ?, ?)
""",
    repo_data_list,
)
conn.commit()

print("\n--- SQLiteデータベースからの全件抽出結果 ---")
cursor.execute("SELECT * FROM repositories")
rows = cursor.fetchall()

for row in rows:
  print(f"ID: {row[0]} | 名前: {row[1]} | 言語: {row[2]} | スター数: {row[3]}")

conn.close()