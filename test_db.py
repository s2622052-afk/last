import os
import sqlite3

# 現在のフォルダ（last）の中に db というフォルダを作る
path = './db/'
os.makedirs(path, exist_ok=True)

db_name = 'test.sqlite'

# DBに接続・作成
con = sqlite3.connect(path + db_name)
con.close()
