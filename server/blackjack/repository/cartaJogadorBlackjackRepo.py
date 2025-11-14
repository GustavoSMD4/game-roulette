import sqlite3
import uuid
from configs.configs import Configs
from server.blackjack.models.cartaJogadorBlackjackModel import CartaJogadorBlackjack


class CartaJogadorBlackjackRepo:
    def __init__(self, conn: sqlite3.Connection):
        self.__conn = conn
        self.__cursor = conn.cursor()

    @classmethod
    def newRepo(cls):
        return cls(sqlite3.Connection(Configs.newConfigs().getCaminhoDB(), check_same_thread=False))

    def createCarta(self, idJogo: str, idJogador: str, idCarta: str):
        idRegistro = str(uuid.uuid4())
        
        self.__cursor.execute("""
            INSERT INTO CARTA_JOGADOR_BLACKJACK (ID, ID_JOGO, ID_JOGADOR, ID_CARTA)
            VALUES (?, ?, ?, ?)
        """, (idRegistro, idJogo, idJogador, idCarta))
        
        self.__conn.commit()
        return self.consultarCarta(idRegistro)

    def consultarCarta(self, idRegistro: str):
        self.__cursor.execute("""
            SELECT * FROM CARTA_JOGADOR_BLACKJACK WHERE ID = ?
        """, (idRegistro,))
        
        resultado = self.__formatar()
        
        if resultado:
            return CartaJogadorBlackjack.newModel(resultado[0])
        
        return None

    def consultarCartasJogador(self, idJogo: str, idJogador: str):
        self.__cursor.execute("""
            SELECT * FROM CARTA_JOGADOR_BLACKJACK 
            WHERE ID_JOGO = ? AND ID_JOGADOR = ?
        """, (idJogo, idJogador))
        
        resultados = self.__formatar()
        return [CartaJogadorBlackjack.newModel(r) for r in resultados]

    def consultarCartasJogo(self, idJogo: str):
        self.__cursor.execute("""
            SELECT * FROM CARTA_JOGADOR_BLACKJACK 
            WHERE ID_JOGO = ?
        """, (idJogo,))
        
        resultados = self.__formatar()
        
        return [CartaJogadorBlackjack.newModel(r) for r in resultados]

    def deletarCarta(self, idRegistro: str):
        self.__cursor.execute("""
            DELETE FROM CARTA_JOGADOR_BLACKJACK WHERE ID = ?
        """, (idRegistro,))
        
        self.__conn.commit()
        
    def deletarTodasCartasJogo(self, idJogo: str):
        self.__cursor.execute("""
            DELETE FROM CARTA_JOGADOR_BLACKJACK WHERE ID_JOGO = ?
        """, (idJogo,))
        
        self.__conn.commit()

    def __formatar(self):
        headers = [desc[0].lower() for desc in self.__cursor.description]
        dadosFormatados = [dict(zip(headers, data)) for data in self.__cursor.fetchall()]
        return dadosFormatados
