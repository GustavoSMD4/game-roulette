import sqlite3
from configs.configs import Configs
from classes.maoBlackjack import MaoBlackjack


class MaoBlackjackRepo:
    def __init__(self, conexao: sqlite3.Connection):
        self.__conn = conexao
        self.__garantirTabela()

    @classmethod
    def newRepo(cls):
        return cls(sqlite3.connect(Configs.newConfigs().getCaminhoDB(), check_same_thread=False))

    def __cursor(self) -> sqlite3.Cursor:
        return self.__conn.cursor()

    def __garantirTabela(self):
        self.__conn.execute("""
            CREATE TABLE IF NOT EXISTS MAOS_BLACKJACK (
                ID INTEGER PRIMARY KEY AUTOINCREMENT,
                ID_JOGO TEXT NOT NULL,
                INDICE INTEGER NOT NULL,
                NOME TEXT,
                VALOR_APOSTA REAL NOT NULL DEFAULT 0,
                ENCERRADA INTEGER NOT NULL DEFAULT 0
            );
        """)
        self.__conn.commit()

    def create(self, idJogo: str, mao: MaoBlackjack):
        cursor = self.__cursor()
        cursor.execute(
            """
            INSERT INTO MAOS_BLACKJACK (ID_JOGO, INDICE, NOME, VALOR_APOSTA, ENCERRADA)
            VALUES (?, ?, ?, ?, ?);
            """,
            (idJogo, mao.getIndice(), mao.getNome(), mao.getValorAposta(), 1 if mao.isEncerrada() else 0)
        )
        self.__conn.commit()

    def atualizar(self, idJogo: str, mao: MaoBlackjack):
        cursor = self.__cursor()
        cursor.execute(
            """
            UPDATE MAOS_BLACKJACK SET NOME = ?, VALOR_APOSTA = ?, ENCERRADA = ?
            WHERE ID_JOGO = ? AND INDICE = ?;
            """,
            (mao.getNome(), mao.getValorAposta(), 1 if mao.isEncerrada() else 0, idJogo, mao.getIndice())
        )
        self.__conn.commit()

    def consultarPorJogo(self, idJogo: str):
        cursor = self.__cursor()
        cursor.execute("SELECT * FROM MAOS_BLACKJACK WHERE ID_JOGO = ? ORDER BY INDICE ASC;", (idJogo,))
        return [MaoBlackjack.newMao(registro) for registro in self.__formatar(cursor)]

    def deletarPorJogo(self, idJogo: str):
        cursor = self.__cursor()
        cursor.execute("DELETE FROM MAOS_BLACKJACK WHERE ID_JOGO = ?;", (idJogo,))
        self.__conn.commit()

    def __formatar(self, cursor: sqlite3.Cursor):
        headers = [desc[0].lower() for desc in cursor.description]
        return [dict(zip(headers, data)) for data in cursor.fetchall()]
