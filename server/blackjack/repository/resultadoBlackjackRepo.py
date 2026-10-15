import sqlite3
from configs.configs import Configs
from server.blackjack.models.resultadoBlackjackModel import ResultadoBlackjack
from utils import agoraBrasilia


class ResultadoBlackjackRepo:
    def __init__(self, conexao: sqlite3.Connection):
        self.__conn = conexao
        self.__garantirTabela()
        self.__garantirColunaIdJogo()

    @classmethod
    def newRepo(cls):
        return cls(sqlite3.connect(Configs.newConfigs().getCaminhoDB(), check_same_thread=False))

    def __cursor(self) -> sqlite3.Cursor:
        return self.__conn.cursor()

    def __garantirTabela(self):
        self.__conn.execute("""
            CREATE TABLE IF NOT EXISTS RESULTADOS_BLACKJACK (
                ID INTEGER PRIMARY KEY AUTOINCREMENT,
                ID_JOGO TEXT,
                ID_JOGADOR TEXT NOT NULL,
                INDICE_MAO INTEGER NOT NULL DEFAULT 0,
                VALOR_APOSTA REAL NOT NULL DEFAULT 0,
                RESULTADO TEXT NOT NULL,
                VALOR_JOGADOR INTEGER NOT NULL DEFAULT 0,
                VALOR_DEALER INTEGER NOT NULL DEFAULT 0,
                VALOR_RECEBIDO REAL NOT NULL DEFAULT 0,
                LUCRO REAL NOT NULL DEFAULT 0,
                DATA_HORA TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        self.__conn.commit()

    def __garantirColunaIdJogo(self):
        colunas = [linha[1] for linha in self.__conn.execute("PRAGMA table_info(RESULTADOS_BLACKJACK)").fetchall()]

        if colunas and "ID_JOGO" not in colunas:
            self.__conn.execute("ALTER TABLE RESULTADOS_BLACKJACK ADD COLUMN ID_JOGO TEXT")
            self.__conn.commit()

        if colunas and "INDICE_MAO" not in colunas:
            self.__conn.execute("ALTER TABLE RESULTADOS_BLACKJACK ADD COLUMN INDICE_MAO INTEGER NOT NULL DEFAULT 0")
            self.__conn.commit()

    def consultarTodos(self):
        cursor = self.__cursor()
        cursor.execute("SELECT * FROM RESULTADOS_BLACKJACK;")
        return [ResultadoBlackjack.newModel(reg) for reg in self.__formatar(cursor)]

    def consultarPorIdJogador(self, idJogador: str):
        cursor = self.__cursor()
        cursor.execute("SELECT * FROM RESULTADOS_BLACKJACK WHERE ID_JOGADOR = ?;", (idJogador,))
        return [ResultadoBlackjack.newModel(reg) for reg in self.__formatar(cursor)]

    def consultarPorJogo(self, idJogo: str, indiceMao: int = 0):
        cursor = self.__cursor()
        cursor.execute(
            "SELECT * FROM RESULTADOS_BLACKJACK WHERE ID_JOGO = ? AND INDICE_MAO = ? ORDER BY ID DESC LIMIT 1;",
            (idJogo, indiceMao)
        )
        dados = self.__formatar(cursor)

        return ResultadoBlackjack.newModel(dados[0]) if dados else None

    def consultarUltimosPorJogador(self, idJogador: str, limite: int = 20):
        cursor = self.__cursor()
        cursor.execute(
            """
            SELECT * FROM RESULTADOS_BLACKJACK
            WHERE ID_JOGADOR = ?
            ORDER BY ID DESC
            LIMIT ?;
            """,
            (idJogador, limite)
        )
        return [ResultadoBlackjack.newModel(reg) for reg in self.__formatar(cursor)]

    def create(self, resultado: ResultadoBlackjack):
        cursor = self.__cursor()
        cursor.execute(
            """
            INSERT INTO RESULTADOS_BLACKJACK
            (ID_JOGO, ID_JOGADOR, INDICE_MAO, VALOR_APOSTA, RESULTADO, VALOR_JOGADOR, VALOR_DEALER, VALOR_RECEBIDO, LUCRO, DATA_HORA)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
            """,
            (
                resultado.getIdJogo(),
                resultado.getIdJogador(),
                resultado.getIndiceMao(),
                resultado.getValorAposta(),
                resultado.getResultado(),
                resultado.getValorJogador(),
                resultado.getValorDealer(),
                resultado.getValorRecebido(),
                resultado.getLucro(),
                resultado.getDataHora() or agoraBrasilia()
            )
        )
        self.__conn.commit()

    def __formatar(self, cursor: sqlite3.Cursor):
        headers = [desc[0].lower() for desc in cursor.description]
        return [dict(zip(headers, data)) for data in cursor.fetchall()]
