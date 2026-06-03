import sqlite3

conn = sqlite3.connect("financeiro.db")

conn.execute("PRAGMA journal_mode=WAL;")

modo = conn.execute("PRAGMA journal_mode;").fetchone()[0]

print("Modo atual:", modo)

conn.close()