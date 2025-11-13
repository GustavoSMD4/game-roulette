

import sqlite3
import uuid

from configs.configs import Configs
from server.blackjack.models.blackjackModel import BlackjackModel
from server.blackjack.models.jogadorBlackjackModel import JogadorBlackjackModel


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
        
        if len(self.__formatar()) <= 0:
            return None
        
        return BlackjackModel.newBlackjackModel(self.__formatar()[0])
    
    def consultarJogoIdJogador(self, idJogador):
        self.__cursor.execute("""
        SELECT J.NOME, J.VALOR_MAO, CJ.RANK, CJ.SUIT FROM JOGADOR_BLACKJACK J
        INNER JOIN CARTA_JOGADOR_BLACKJACK CJ ON J.ID_JOGO = CJ.ID_JOGO
        WHERE J.JOGADOR_HOST = ?
        """, (idJogador, ))
        
        if len(self.__formatar()) <= 0:
            return None
        
        return BlackjackModel.newBlackjackModel(self.__formatar()[0])
    
    def consultaJogador(self, idJogador):
        self.__cursor.execute("""
        SELECT J.NOME, J.VALOR_MAO, CJ.RANK, CJ.SUIT FROM JOGADOR_BLACKJACK J
        INNER JOIN CARTA_JOGADOR_BLACKJACK CJ ON J.ID_JOGO = CJ.ID_JOGO
        WHERE J.ID = ?
        """, (idJogador, ))
        
        return self.__formatar()
    
    def consultarJogadores(self, idJogo):
        self.__cursor.execute("SELECT * FROM JOGADOR_BLACKJACK WHERE ID_JOGO = ?", (idJogo, ))
        self.__conn.commit()
        return self.__formatar()
    
    def createNovoJogo(self, jogo: BlackjackModel):
        self.__cursor.execute("INSERT INTO BLACKJACK VALUES (?, ?)", (jogo.getId(), jogo.getIdJogador()))
        self.__conn.commit()
        return BlackjackModel.newBlackjackModel(self.consultarJogo(jogo.getId()))
    
    def createJogador(self, idJogo, jogador: JogadorBlackjackModel):
        self.__cursor.execute("INSERT INTO JOGADOR_BLACKJACK (ID_JOGO, NOME) VALUES (?, ?)", (idJogo, jogador.getNome()))
        self.__conn.commit()
    
    def __formatar(self):
        headers = [desc[0].lower() for desc in self.__cursor.description]
        dadosFormatados = [dict(zip(headers, data)) for data in self.__cursor.fetchall()]
        return dadosFormatados