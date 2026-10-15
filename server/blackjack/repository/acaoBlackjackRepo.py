import sqlite3
from configs.configs import Configs
from server.blackjack.models.acaoBlackjackModel import AcaoBlackjack
from utils import agoraBrasilia


class AcaoBlackjackRepo:
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
            CREATE TABLE IF NOT EXISTS ACOES_BLACKJACK (
                ID INTEGER PRIMARY KEY AUTOINCREMENT,
                ID_JOGO TEXT NOT NULL,
                ID_JOGADOR TEXT,
                INDICE_MAO INTEGER NOT NULL DEFAULT 0,
                ACAO TEXT NOT NULL,
                DONO TEXT NOT NULL,
                CARTA TEXT,
                VALOR_JOGADOR INTEGER NOT NULL DEFAULT 0,
                VALOR_DEALER INTEGER NOT NULL DEFAULT 0,
                DATA_HORA TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        self.__conn.commit()
        self.__garantirColunaIndiceMao()

    def __garantirColunaIndiceMao(self):
        colunas = [linha[1] for linha in self.__conn.execute("PRAGMA table_info(ACOES_BLACKJACK)").fetchall()]

        if colunas and "INDICE_MAO" not in colunas:
            self.__conn.execute("ALTER TABLE ACOES_BLACKJACK ADD COLUMN INDICE_MAO INTEGER NOT NULL DEFAULT 0")
            self.__conn.commit()

    def create(self, acao: AcaoBlackjack):
        cursor = self.__cursor()
        cursor.execute(
            """
            INSERT INTO ACOES_BLACKJACK
            (ID_JOGO, ID_JOGADOR, INDICE_MAO, ACAO, DONO, CARTA, VALOR_JOGADOR, VALOR_DEALER, DATA_HORA)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);
            """,
            (
                acao.getIdJogo(),
                acao.getIdJogador(),
                acao.getIndiceMao(),
                acao.getAcao(),
                acao.getDono(),
                acao.getCarta(),
                acao.getValorJogador(),
                acao.getValorDealer(),
                acao.getDataHora() or agoraBrasilia()
            )
        )
        self.__conn.commit()

    def consultarPorJogo(self, idJogo: str, indiceMao: int = 0):
        cursor = self.__cursor()
        # INDICE_MAO = -1 guarda as ações do dealer, comuns a todas as mãos
        cursor.execute(
            """
            SELECT * FROM ACOES_BLACKJACK
            WHERE ID_JOGO = ? AND (INDICE_MAO = ? OR INDICE_MAO = -1)
            ORDER BY ID ASC;
            """,
            (idJogo, indiceMao)
        )
        return [AcaoBlackjack.newModel(reg) for reg in self.__formatar(cursor)]

    def __formatar(self, cursor: sqlite3.Cursor):
        headers = [desc[0].lower() for desc in cursor.description]
        return [dict(zip(headers, data)) for data in cursor.fetchall()]
