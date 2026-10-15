import sqlite3
from configs.configs import Configs
from server.roulette.models.resultadoRoletaModel import ResultadoRoleta
from utils import agoraBrasilia


class ResultadoRoletaRepo:
    def __init__(self, configs, conexao: sqlite3.Connection):
        self.configs = configs
        self.__conn = conexao
        self.__cursor = conexao.cursor()

    @classmethod
    def newRepo(cls):
        configs = Configs.newConfigs()
        return cls(configs, sqlite3.connect(configs.getCaminhoDB(), check_same_thread=False))

    def consultarTodos(self):
        self.__cursor.execute("SELECT * FROM RESULTADOS_ROLETA;")
        return [ResultadoRoleta.newModel(reg) for reg in self.__formatar()]

    def consultarPorIdJogador(self, idJogador: str):
        self.__cursor.execute("SELECT * FROM RESULTADOS_ROLETA WHERE ID_JOGADOR = ?;", (idJogador,))
        dados = self.__formatar()
        return [ResultadoRoleta.newModel(reg) for reg in dados]

    def consultarPorResultado(self, resultado: str):
        self.__cursor.execute("SELECT * FROM RESULTADOS_ROLETA WHERE RESULTADO = ?;", (resultado,))
        dados = self.__formatar()
        return [ResultadoRoleta.newModel(reg) for reg in dados]

    def create(self, resultado: ResultadoRoleta):
        sql = """
            INSERT INTO RESULTADOS_ROLETA 
            (ID_JOGADOR, APOSTA_JOGADOR, VALOR_APOSTA, RESULTADO, VALOR_RESULTADO, GANHOU, DATA_HORA)
            VALUES (?, ?, ?, ?, ?, ?, ?);
        """
        dados = (
            resultado.getIdJogador(),
            resultado.getApostaJogador(),
            resultado.getValorAposta(),
            resultado.getResultado(),
            resultado.getValorResultado(),
            resultado.getGanhou(),
            resultado.getDataHora() or agoraBrasilia()
        )
        self.__cursor.execute(sql, dados)
        self.__conn.commit()

    def update(self, resultado: ResultadoRoleta):
        sql = """
            UPDATE RESULTADOS_ROLETA
            SET APOSTA_JOGADOR = ?, VALOR_APOSTA = ?, RESULTADO = ?, VALOR_RESULTADO = ?, GANHOU = ?
            WHERE ID_JOGADOR = ?;
        """
        dados = (
            resultado.getApostaJogador(),
            resultado.getValorAposta(),
            resultado.getResultado(),
            resultado.getValorResultado(),
            resultado.getGanhou(),
            resultado.getIdJogador()
        )
        self.__cursor.execute(sql, dados)
        self.__conn.commit()

    def deletePorJogador(self, idJogador: str):
        sql = "DELETE FROM RESULTADOS_ROLETA WHERE ID_JOGADOR = ?;"
        self.__cursor.execute(sql, (idJogador,))
        self.__conn.commit()

    def existeResultadoPorJogador(self, idJogador: str):
        self.__cursor.execute("SELECT 1 FROM RESULTADOS_ROLETA WHERE ID_JOGADOR = ?;", (idJogador,))
        return self.__cursor.fetchone() is not None

    def consultarUltimosPorJogador(self, idJogador: str, limite: int = 10):
        sql = """
            SELECT * FROM RESULTADOS_ROLETA
            WHERE ID_JOGADOR = ?
            ORDER BY DATA_HORA DESC
            LIMIT ?;
        """
        self.__cursor.execute(sql, (idJogador, limite))
        return [ResultadoRoleta.newModel(reg) for reg in self.__formatar()]

    def __formatar(self):
        headers = [desc[0].lower() for desc in self.__cursor.description]
        dadosFormatados = [dict(zip(headers, data)) for data in self.__cursor.fetchall()]
        return dadosFormatados

    def __formatarOne(self, row):
        headers = [desc[0].lower() for desc in self.__cursor.description]
        return dict(zip(headers, row))
