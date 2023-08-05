# python table.py

import sqlite3
from tabulate import tabulate

conn = sqlite3.connect('static/dbs/main.db')
cur = conn.cursor()

# Посмотреть данные из базы
# cur.execute("SELECT * FROM users")
# cur.execute("SELECT * FROM posts")
# rows = cur.fetchall()
# print(rows)

# headers = [description[0] for description in cur.description]

# table = tabulate(rows, headers, tablefmt="grid")
# print(table)


# cur.execute("DELETE FROM posts WHERE id = 4")
# conn.commit()
# cur.execute("SELECT * FROM posts")
# print(cur.fetchall()[0])

cur.close()
conn.close()
