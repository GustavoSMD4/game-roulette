import sqlite3
import uuid
import sys
import os
sys.path.append(os.getcwd())
from classes.baralho import Baralho


conn = sqlite3.connect("server/database/database.db", check_same_thread=False)
cursor = conn.cursor()

# Cria tabela CARTA se não existir
cursor.execute("""
CREATE TABLE IF NOT EXISTS CARTA (
    ID VARCHAR(36) PRIMARY KEY,
    RANK VARCHAR(2) NOT NULL,
    SUIT VARCHAR(10) NOT NULL,
    VALOR INTEGER NOT NULL,
    NOME_IMAGEM TEXT NOT NULL
);
""")

# Gera um baralho (1 baralho padrão)
baralho = Baralho.newBaralho(1)
cartas = baralho.getCartas()

# Popula a tabela
for carta in cartas:
    id_carta = str(uuid.uuid4())  # gera ID único
    cursor.execute("""
        INSERT INTO CARTA (ID, RANK, SUIT, VALOR, NOME_IMAGEM)
        VALUES (?, ?, ?, ?, ?)
    """, (id_carta, carta.getRank(), carta.getSuit(), carta.getValor(), carta.getNomeImagem()))

conn.commit()
conn.close()

print("Tabela CARTA populada com sucesso!")