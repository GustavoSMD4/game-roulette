import sqlite3
from classes.carta import Carta
from configs.configs import Configs

class CartaRepo:
    def __init__(self, configs, conexao: sqlite3.Connection):
        self.configs = configs
        self.__conn = conexao
        self.__cursor = conexao.cursor()

    @classmethod
    def newRepo(cls):
        configs = Configs.newConfigs()
        return cls(configs, sqlite3.connect(configs.getCaminhoDB(), check_same_thread=False))

    def consultarTodos(self):
        self.__cursor.execute("SELECT * FROM CARTA;")
        return [Carta.newCarta(reg) for reg in self.__formatar()]

    def consultarPorId(self, idCarta: str):
        self.__cursor.execute("SELECT * FROM CARTA WHERE ID = ?;", (idCarta,))
        dados = self.__formatar()
        return Carta.newCarta(dados[0]) if dados else None

    def consultarPorNaipe(self, suit: str):
        self.__cursor.execute("SELECT * FROM CARTA WHERE SUIT = ?;", (suit,))
        return [Carta.newCarta(reg) for reg in self.__formatar()]

    def consultarPorRank(self, rank: str):
        self.__cursor.execute("SELECT * FROM CARTA WHERE RANK = ?;", (rank,))
        return [Carta.newCarta(reg) for reg in self.__formatar()]

    def create(self, carta: Carta):
        sql = """
            INSERT INTO CARTA (ID, RANK, SUIT, VALOR, NOME_IMAGEM)
            VALUES (?, ?, ?, ?, ?);
        """
        dados = (
            carta.getId(),
            carta.getRank(),
            carta.getSuit(),
            carta.getValor(),
            carta.getNomeImagem()
        )
        self.__cursor.execute(sql, dados)
        self.__conn.commit()

    def update(self, carta: Carta):
        sql = """
            UPDATE CARTA
            SET RANK = ?, SUIT = ?, VALOR = ?, NOME_IMAGEM = ?
            WHERE ID = ?;
        """
        dados = (
            carta.getRank(),
            carta.getSuit(),
            carta.getValor(),
            carta.getNomeImagem(),
            carta.getId()
        )
        self.__cursor.execute(sql, dados)
        self.__conn.commit()

    def deletePorId(self, idCarta: str):
        sql = "DELETE FROM CARTA WHERE ID = ?;"
        self.__cursor.execute(sql, (idCarta,))
        self.__conn.commit()

    def existeCartaPorId(self, idCarta: str):
        self.__cursor.execute("SELECT 1 FROM CARTA WHERE ID = ?;", (idCarta,))
        return self.__cursor.fetchone() is not None

    def consultarPorValor(self, valor: int):
        self.__cursor.execute("SELECT * FROM CARTA WHERE VALOR = ?;", (valor,))
        return [Carta.newCarta(reg) for reg in self.__formatar()]

    def __formatar(self):
        headers = [desc[0].lower() for desc in self.__cursor.description]
        dadosFormatados = [dict(zip(headers, data)) for data in self.__cursor.fetchall()]
        return dadosFormatados

    def __formatarOne(self, row):
        headers = [desc[0].lower() for desc in self.__cursor.description]
        return dict(zip(headers, row))
