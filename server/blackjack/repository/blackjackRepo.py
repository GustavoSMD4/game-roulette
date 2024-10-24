

import sqlite3

from configs.configs import Configs


class BlackjackRepo:
    def __init__(self, conn: sqlite3.Connection):
        self.__conn = conn
        self.__cursor = conn.cursor()
        
    @classmethod
    def newBlackjackRepo(cls):
        return cls(sqlite3.Connection(Configs.newConfigs().getCaminhoDB(), check_same_thread=False))
    
    def consultarJogo(self, idJogo):
        self.__cursor.execute("""
        SELECT J.NOME, J.VALOR_MAO, CJ.RANK, CJ.SUIT FROM JOGADOR_BLACKJACK J
        INNER JOIN CARTA_JOGADOR_BLACKJACK CJ ON J.ID_JOGO = CJ.ID_JOGO
        WHERE J.ID_JOGO = ?
        """, (idJogo, ))
        
        return self.__formatar()
    
    
    def consultaJogador(self, idJogo, idJogador):
        self.__cursor.execute("""
        SELECT J.NOME, J.VALOR_MAO, CJ.RANK, CJ.SUIT FROM JOGADOR_BLACKJACK J
        INNER JOIN CARTA_JOGADOR_BLACKJACK CJ ON J.ID_JOGO = CJ.ID_JOGO
        WHERE J.ID_JOGO = ? and J.ID = ?
        """, (idJogo, idJogador))
        
        return self.__formatar()
    
        
    def __formatar(self):
        headers = [desc[0].lower() for desc in self.__cursor.description]
        dadosFormatados = [dict(zip(headers, data)) for data in self.__cursor.fetchall()]
        return dadosFormatados