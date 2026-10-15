import sqlite3
from configs.configs import Configs
from server.roulette.models.rodadaRoletaModel import RodadaRoleta


class RodadaRoletaRepo:
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
            CREATE TABLE IF NOT EXISTS RODADAS_ROLETA (
                ID INTEGER PRIMARY KEY AUTOINCREMENT,
                DATA_HORA_INICIO TEXT NOT NULL,
                DATA_HORA_FECHAMENTO TEXT NOT NULL,
                NUMERO INTEGER,
                COR TEXT,
                ID_SESSAO INTEGER
            );
        """)

        colunas = [linha[1] for linha in self.__conn.execute("PRAGMA table_info(RODADAS_ROLETA)").fetchall()]

        if "ID_SESSAO" not in colunas:
            self.__conn.execute("ALTER TABLE RODADAS_ROLETA ADD COLUMN ID_SESSAO INTEGER")

        self.__conn.commit()

    def criar(self, dataHoraInicio, dataHoraFechamento, idSessao=None):
        cursor = self.__cursor()
        cursor.execute(
            """
            INSERT INTO RODADAS_ROLETA (DATA_HORA_INICIO, DATA_HORA_FECHAMENTO, ID_SESSAO) VALUES (?, ?, ?);
            """,
            (
                dataHoraInicio.strftime("%Y-%m-%d %H:%M:%S"),
                dataHoraFechamento.strftime("%Y-%m-%d %H:%M:%S"),
                idSessao
            )
        )
        self.__conn.commit()
        return self.consultarPorId(cursor.lastrowid)

    def registrarSorteio(self, idRodada: int, numero: int, cor: str):
        cursor = self.__cursor()
        cursor.execute(
            "UPDATE RODADAS_ROLETA SET NUMERO = ?, COR = ? WHERE ID = ?;",
            (numero, cor, idRodada)
        )
        self.__conn.commit()
        return self.consultarPorId(idRodada)

    def consultarUltima(self, idSessao=None):
        cursor = self.__cursor()
        filtro, parametros = self.__filtroSessao(idSessao)
        cursor.execute(f"SELECT * FROM RODADAS_ROLETA WHERE {filtro} ORDER BY ID DESC LIMIT 1;", parametros)
        dados = self.__formatar(cursor)
        return RodadaRoleta.newModel(dados[0]) if dados else None

    def consultarPorId(self, idRodada: int):
        cursor = self.__cursor()
        cursor.execute("SELECT * FROM RODADAS_ROLETA WHERE ID = ?;", (idRodada,))
        dados = self.__formatar(cursor)
        return RodadaRoleta.newModel(dados[0]) if dados else None

    def consultarSorteadas(self, idSessao=None, limite: int = 12):
        cursor = self.__cursor()
        filtro, parametros = self.__filtroSessao(idSessao)
        cursor.execute(
            f"SELECT * FROM RODADAS_ROLETA WHERE {filtro} AND NUMERO IS NOT NULL ORDER BY ID DESC LIMIT ?;",
            tuple(parametros) + (limite,)
        )
        return [RodadaRoleta.newModel(registro) for registro in self.__formatar(cursor)]

    def consultarNaoSorteadas(self, idSessao=None, limite: int = 5):
        cursor = self.__cursor()
        filtro, parametros = self.__filtroSessao(idSessao)
        cursor.execute(
            f"SELECT * FROM RODADAS_ROLETA WHERE {filtro} AND NUMERO IS NULL ORDER BY ID DESC LIMIT ?;",
            tuple(parametros) + (limite,)
        )
        return [RodadaRoleta.newModel(registro) for registro in self.__formatar(cursor)]

    def consultarIdsPorSessao(self, idSessao: int):
        cursor = self.__cursor()
        cursor.execute("SELECT ID FROM RODADAS_ROLETA WHERE ID_SESSAO = ?;", (idSessao,))
        return [linha[0] for linha in cursor.fetchall()]

    def deletarPorSessao(self, idSessao: int):
        cursor = self.__cursor()
        cursor.execute("DELETE FROM RODADAS_ROLETA WHERE ID_SESSAO = ?;", (idSessao,))
        self.__conn.commit()

    @staticmethod
    def __filtroSessao(idSessao):
        if idSessao is None:
            return "ID_SESSAO IS NULL", ()

        return "ID_SESSAO = ?", (idSessao,)

    def __formatar(self, cursor: sqlite3.Cursor):
        headers = [desc[0].lower() for desc in cursor.description]
        return [dict(zip(headers, data)) for data in cursor.fetchall()]
