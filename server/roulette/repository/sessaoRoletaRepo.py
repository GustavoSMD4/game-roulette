import sqlite3
import uuid
from configs.configs import Configs
from server.roulette.models.sessaoRoletaModel import SessaoRoleta


class SessaoRoletaRepo:
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
            CREATE TABLE IF NOT EXISTS SESSOES_ROLETA (
                ID INTEGER PRIMARY KEY AUTOINCREMENT,
                CODIGO TEXT NOT NULL UNIQUE,
                NOME TEXT NOT NULL,
                ID_CRIADOR TEXT,
                DATA_HORA_CRIACAO TEXT NOT NULL,
                DATA_HORA_EXPIRACAO TEXT NOT NULL
            );
        """)
        self.__conn.commit()

    def criar(self, nome: str, idCriador, dataHoraCriacao, dataHoraExpiracao):
        cursor = self.__cursor()

        for _ in range(5):
            codigo = uuid.uuid4().hex[:8].upper()

            try:
                cursor.execute(
                    """
                    INSERT INTO SESSOES_ROLETA (CODIGO, NOME, ID_CRIADOR, DATA_HORA_CRIACAO, DATA_HORA_EXPIRACAO)
                    VALUES (?, ?, ?, ?, ?);
                    """,
                    (
                        codigo,
                        nome,
                        str(idCriador) if idCriador is not None else None,
                        dataHoraCriacao.strftime("%Y-%m-%d %H:%M:%S"),
                        dataHoraExpiracao.strftime("%Y-%m-%d %H:%M:%S")
                    )
                )
                self.__conn.commit()
                return self.consultarPorCodigo(codigo)
            except sqlite3.IntegrityError:
                continue

        raise Exception("Não foi possível gerar o código da sessão. Tente novamente.")

    def consultarPorCodigo(self, codigo: str):
        if not codigo:
            return None

        cursor = self.__cursor()
        cursor.execute("SELECT * FROM SESSOES_ROLETA WHERE CODIGO = ?;", (str(codigo).strip().upper(),))
        dados = self.__formatar(cursor)
        return SessaoRoleta.newModel(dados[0]) if dados else None

    def consultarExpiradas(self, agora):
        cursor = self.__cursor()
        cursor.execute(
            "SELECT * FROM SESSOES_ROLETA WHERE DATA_HORA_EXPIRACAO <= ?;",
            (agora.strftime("%Y-%m-%d %H:%M:%S"),)
        )
        return [SessaoRoleta.newModel(registro) for registro in self.__formatar(cursor)]

    def deletar(self, idSessao: int):
        cursor = self.__cursor()
        cursor.execute("DELETE FROM SESSOES_ROLETA WHERE ID = ?;", (idSessao,))
        self.__conn.commit()

    def __formatar(self, cursor: sqlite3.Cursor):
        headers = [desc[0].lower() for desc in cursor.description]
        return [dict(zip(headers, data)) for data in cursor.fetchall()]
