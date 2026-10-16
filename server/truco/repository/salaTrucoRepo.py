import sqlite3
import uuid
from configs.configs import Configs
from server.truco.models.salaTrucoModel import SalaTruco


class SalaTrucoRepo:
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
            CREATE TABLE IF NOT EXISTS SALAS_TRUCO (
                ID INTEGER PRIMARY KEY AUTOINCREMENT,
                CODIGO TEXT NOT NULL UNIQUE,
                NOME TEXT NOT NULL,
                MODO TEXT NOT NULL DEFAULT '2x2',
                ID_CRIADOR TEXT,
                DATA_HORA_CRIACAO TEXT NOT NULL,
                DATA_HORA_EXPIRACAO TEXT NOT NULL
            );
        """)
        self.__conn.commit()

    def criar(self, nome: str, modo: str, idCriador, dataHoraCriacao, dataHoraExpiracao):
        cursor = self.__cursor()

        for _ in range(5):
            codigo = uuid.uuid4().hex[:8].upper()

            try:
                cursor.execute(
                    """
                    INSERT INTO SALAS_TRUCO (CODIGO, NOME, MODO, ID_CRIADOR, DATA_HORA_CRIACAO, DATA_HORA_EXPIRACAO)
                    VALUES (?, ?, ?, ?, ?, ?);
                    """,
                    (
                        codigo,
                        nome,
                        modo,
                        str(idCriador) if idCriador is not None else None,
                        dataHoraCriacao.strftime("%Y-%m-%d %H:%M:%S"),
                        dataHoraExpiracao.strftime("%Y-%m-%d %H:%M:%S")
                    )
                )
                self.__conn.commit()
                return self.consultarPorCodigo(codigo)
            except sqlite3.IntegrityError:
                continue

        raise Exception("Não foi possível gerar o código da sala. Tente novamente.")

    def consultarPorCodigo(self, codigo: str):
        if not codigo:
            return None

        cursor = self.__cursor()
        cursor.execute("SELECT * FROM SALAS_TRUCO WHERE CODIGO = ?;", (str(codigo).strip().upper(),))
        dados = self.__formatar(cursor)
        return SalaTruco.newModel(dados[0]) if dados else None

    def consultarExpiradas(self, agora):
        cursor = self.__cursor()
        cursor.execute(
            "SELECT * FROM SALAS_TRUCO WHERE DATA_HORA_EXPIRACAO <= ?;",
            (agora.strftime("%Y-%m-%d %H:%M:%S"),)
        )
        return [SalaTruco.newModel(registro) for registro in self.__formatar(cursor)]

    def deletar(self, idSala: int):
        cursor = self.__cursor()
        cursor.execute("DELETE FROM SALAS_TRUCO WHERE ID = ?;", (idSala,))
        self.__conn.commit()

    def __formatar(self, cursor: sqlite3.Cursor):
        headers = [desc[0].lower() for desc in cursor.description]
        return [dict(zip(headers, data)) for data in cursor.fetchall()]
