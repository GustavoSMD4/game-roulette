import json
import sqlite3
from configs.configs import Configs
from server.truco.models.partidaTrucoModel import PartidaTruco


class PartidaTrucoRepo:
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
            CREATE TABLE IF NOT EXISTS PARTIDAS_TRUCO (
                ID INTEGER PRIMARY KEY AUTOINCREMENT,
                ID_SALA INTEGER NOT NULL,
                FASE TEXT NOT NULL,
                DATA_HORA_INICIO TEXT NOT NULL,
                DATA_HORA_FIM_FASE TEXT NOT NULL,
                ESTADO TEXT NOT NULL
            );
        """)
        self.__conn.execute("CREATE INDEX IF NOT EXISTS IX_PARTIDAS_TRUCO_SALA ON PARTIDAS_TRUCO (ID_SALA);")
        self.__conn.commit()

    def criar(self, idSala: int, fase: str, inicio, fimFase, estado: dict):
        cursor = self.__cursor()
        cursor.execute(
            """
            INSERT INTO PARTIDAS_TRUCO (ID_SALA, FASE, DATA_HORA_INICIO, DATA_HORA_FIM_FASE, ESTADO)
            VALUES (?, ?, ?, ?, ?);
            """,
            (
                idSala,
                fase,
                inicio.strftime("%Y-%m-%d %H:%M:%S"),
                fimFase.strftime("%Y-%m-%d %H:%M:%S"),
                json.dumps(estado)
            )
        )
        self.__conn.commit()
        return self.consultarPorId(cursor.lastrowid)

    def atualizar(self, idPartida: int, fase: str, fimFase, estado: dict):
        cursor = self.__cursor()
        cursor.execute(
            "UPDATE PARTIDAS_TRUCO SET FASE = ?, DATA_HORA_FIM_FASE = ?, ESTADO = ? WHERE ID = ?;",
            (fase, fimFase.strftime("%Y-%m-%d %H:%M:%S"), json.dumps(estado), idPartida)
        )
        self.__conn.commit()
        return self.consultarPorId(idPartida)

    def consultarAtual(self, idSala: int):
        cursor = self.__cursor()
        cursor.execute("SELECT * FROM PARTIDAS_TRUCO WHERE ID_SALA = ? ORDER BY ID DESC LIMIT 1;", (idSala,))
        dados = self.__formatar(cursor)
        return PartidaTruco.newModel(dados[0]) if dados else None

    def consultarPorId(self, idPartida: int):
        cursor = self.__cursor()
        cursor.execute("SELECT * FROM PARTIDAS_TRUCO WHERE ID = ?;", (idPartida,))
        dados = self.__formatar(cursor)
        return PartidaTruco.newModel(dados[0]) if dados else None

    def deletarPorSala(self, idSala: int):
        cursor = self.__cursor()
        cursor.execute("DELETE FROM PARTIDAS_TRUCO WHERE ID_SALA = ?;", (idSala,))
        self.__conn.commit()

    def __formatar(self, cursor: sqlite3.Cursor):
        headers = [desc[0].lower() for desc in cursor.description]
        return [dict(zip(headers, data)) for data in cursor.fetchall()]
