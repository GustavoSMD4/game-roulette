import json
import sqlite3
from configs.configs import Configs
from server.blackjack.models.rodadaBlackjackModel import RodadaBlackjack


class RodadaBlackjackRepo:
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
            CREATE TABLE IF NOT EXISTS RODADAS_BLACKJACK (
                ID INTEGER PRIMARY KEY AUTOINCREMENT,
                ID_SALA INTEGER NOT NULL,
                NUMERO INTEGER NOT NULL,
                FASE TEXT NOT NULL,
                DATA_HORA_INICIO TEXT NOT NULL,
                DATA_HORA_FIM_FASE TEXT NOT NULL,
                ESTADO TEXT NOT NULL
            );
        """)
        self.__conn.execute("CREATE INDEX IF NOT EXISTS IX_RODADAS_BLACKJACK_SALA ON RODADAS_BLACKJACK (ID_SALA);")
        self.__conn.commit()

    def criar(self, idSala: int, fase: str, inicio, fimFase, estado: dict):
        cursor = self.__cursor()
        proximo = cursor.execute(
            "SELECT COALESCE(MAX(NUMERO), 0) + 1 FROM RODADAS_BLACKJACK WHERE ID_SALA = ?;", (idSala,)
        ).fetchone()[0]

        cursor.execute(
            """
            INSERT INTO RODADAS_BLACKJACK (ID_SALA, NUMERO, FASE, DATA_HORA_INICIO, DATA_HORA_FIM_FASE, ESTADO)
            VALUES (?, ?, ?, ?, ?, ?);
            """,
            (
                idSala,
                proximo,
                fase,
                inicio.strftime("%Y-%m-%d %H:%M:%S"),
                fimFase.strftime("%Y-%m-%d %H:%M:%S"),
                json.dumps(estado)
            )
        )
        self.__conn.commit()
        return self.consultarPorId(cursor.lastrowid)

    def atualizar(self, idRodada: int, fase: str, fimFase, estado: dict):
        cursor = self.__cursor()
        cursor.execute(
            "UPDATE RODADAS_BLACKJACK SET FASE = ?, DATA_HORA_FIM_FASE = ?, ESTADO = ? WHERE ID = ?;",
            (fase, fimFase.strftime("%Y-%m-%d %H:%M:%S"), json.dumps(estado), idRodada)
        )
        self.__conn.commit()
        return self.consultarPorId(idRodada)

    def consultarAtual(self, idSala: int):
        cursor = self.__cursor()
        cursor.execute("SELECT * FROM RODADAS_BLACKJACK WHERE ID_SALA = ? ORDER BY ID DESC LIMIT 1;", (idSala,))
        dados = self.__formatar(cursor)
        return RodadaBlackjack.newModel(dados[0]) if dados else None

    def consultarPorId(self, idRodada: int):
        cursor = self.__cursor()
        cursor.execute("SELECT * FROM RODADAS_BLACKJACK WHERE ID = ?;", (idRodada,))
        dados = self.__formatar(cursor)
        return RodadaBlackjack.newModel(dados[0]) if dados else None

    def deletarPorSala(self, idSala: int):
        cursor = self.__cursor()
        cursor.execute("DELETE FROM RODADAS_BLACKJACK WHERE ID_SALA = ?;", (idSala,))
        self.__conn.commit()

    def __formatar(self, cursor: sqlite3.Cursor):
        headers = [desc[0].lower() for desc in cursor.description]
        return [dict(zip(headers, data)) for data in cursor.fetchall()]
