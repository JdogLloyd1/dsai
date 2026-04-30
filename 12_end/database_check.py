# Python
import sqlite3, pandas as pd
db = sqlite3.connect("12_end/data/traffic.db")
print(pd.read_sql("SELECT * FROM traffic", db))
db.close()