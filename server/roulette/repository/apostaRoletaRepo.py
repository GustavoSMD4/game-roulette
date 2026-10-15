import sqlite3
from configs.configs import Configs
from server.roulette.models.apostaRoletaModel import ApostaRoleta


class ApostaRoletaRepo:
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
            CREATE TABLE IF NOT EXISTS APOSTAS_ROLETA (
                ID INTEGER PRIMARY KEY AUTOINCREMENT,
                ID_RODADA INTEGER NOT NULL,
                ID_JOGADOR TEXT NOT NULL,
                NOME TEXT,
                APOSTA TEXT NOT NULL,
                TIPO TEXT NOT NULL,
                VALOR_APOSTA REAL NOT NULL,
                GANHOU INTEGER,
                VALOR_RECEBIDO REAL,
                LUCRO REAL,
                DATA_HORA TEXT NOT NULL
            );
        """)
        self.__conn.execute("CREATE INDEX IF NOT EXISTS IX_APOSTAS_ROLETA_RODADA ON APOSTAS_ROLETA (ID_RODADA);")
        self.__conn.commit()

    def create(self, aposta: ApostaRoleta):
        cursor = self.__cursor()
        cursor.execute(
            """
            INSERT INTO APOSTAS_ROLETA
            (ID_RODADA, ID_JOGADOR, NOME, APOSTA, TIPO, VALOR_APOSTA, DATA_HORA)
            VALUES (?, ?, ?, ?, ?, ?, ?);
            """,
            (
                aposta.getIdRodada(),
                aposta.getIdJogador(),
                aposta.getNome(),
                aposta.getAposta(),
                aposta.getTipo(),
                aposta.getValorAposta(),
                aposta.getDataHora().strftime("%Y-%m-%d %H:%M:%S")
            )
        )
        self.__conn.commit()
        return cursor.lastrowid

    def registrarPagamento(self, idAposta: int, ganhou: int, valorRecebido: float, lucro: float):
        cursor = self.__cursor()
        cursor.execute(
            """
            UPDATE APOSTAS_ROLETA SET GANHOU = ?, VALOR_RECEBIDO = ?, LUCRO = ? WHERE ID = ?;
            """,
            (ganhou, valorRecebido, lucro, idAposta)
        )
        self.__conn.commit()

    def consultarPorRodada(self, idRodada: int):
        cursor = self.__cursor()
        cursor.execute(
            "SELECT * FROM APOSTAS_ROLETA WHERE ID_RODADA = ? ORDER BY ID ASC;",
            (idRodada,)
        )
        return [ApostaRoleta.newModel(registro) for registro in self.__formatar(cursor)]

    def consultarNaoPagas(self, idRodada: int):
        cursor = self.__cursor()
        cursor.execute(
            "SELECT * FROM APOSTAS_ROLETA WHERE ID_RODADA = ? AND GANHOU IS NULL ORDER BY ID ASC;",
            (idRodada,)
        )
        return [ApostaRoleta.newModel(registro) for registro in self.__formatar(cursor)]

    def deletarPorRodadas(self, idsRodadas: list):
        if not idsRodadas:
            return

        marcadores = ",".join("?" for _ in idsRodadas)
        cursor = self.__cursor()
        cursor.execute(f"DELETE FROM APOSTAS_ROLETA WHERE ID_RODADA IN ({marcadores});", tuple(idsRodadas))
        self.__conn.commit()

    def __formatar(self, cursor: sqlite3.Cursor):
        headers = [desc[0].lower() for desc in cursor.description]
        return [dict(zip(headers, data)) for data in cursor.fetchall()]
