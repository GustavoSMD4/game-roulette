import sqlite3

conn = sqlite3.Connection("database/database.db", check_same_thread=False)
cursor = conn.cursor()

def createTable():
    cursor.execute("""
         CREATE TABLE USUARIOS(
	ID INTEGER PRIMARY KEY AUTOINCREMENT,
  	USUARIO VARCHAR(100) NOT NULL UNIQUE,
  	SENHA VARCHAR(100) NOT NULL,
  	SALDO DECIMAL(10, 2) NOT NULL DEFAULT 0
)          
                   """)
    
createTable()

conn.commit()
conn.close()