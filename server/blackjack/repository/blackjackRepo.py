import sqlite3
from configs.configs import Configs
from server.blackjack.models.blackjackModel import BlackjackModel
from server.blackjack.models.jogadorBlackjackModel import JogadorBlackjackModel


class BlackjackRepo:
    def __init__(self, conn: sqlite3.Connection):
        self.__conn = conn
        self.__cursor = conn.cursor()
        self.__garantirColunaValorAposta()
        
    @classmethod
    def newBlackjackRepo(cls):
        return cls(sqlite3.Connection(Configs.newConfigs().getCaminhoDB(), check_same_thread=False))

    def __garantirColunaValorAposta(self):
        colunas = [linha[1] for linha in self.__cursor.execute("PRAGMA table_info(BLACKJACK)").fetchall()]

        if colunas and "VALOR_APOSTA" not in colunas:
            self.__cursor.execute("ALTER TABLE BLACKJACK ADD COLUMN VALOR_APOSTA REAL NOT NULL DEFAULT 0")
            self.__conn.commit()
    
    def consultarJogo(self, idJogo: str):
        self.__cursor.execute(
            "SELECT * FROM BLACKJACK WHERE ID = ?",
            (idJogo,)
        )
        
        resultados = self.__formatar()
        if len(resultados) <= 0:
            return None
        
        return BlackjackModel.newBlackjackModel(resultados[0])
    
    def consultarJogoIdJogador(self, idJogador: str):
        self.__cursor.execute(
            "SELECT * FROM BLACKJACK WHERE JOGADOR_HOST = ?",
            (idJogador,)
        )
        resultados = self.__formatar()
        if not resultados:
            return None
        return BlackjackModel.newBlackjackModel(resultados[0])
    
    def consultarJogadores(self, idJogo: str):
        self.__cursor.execute(
            "SELECT ID, ID_JOGO, NOME, VALOR_MAO FROM JOGADOR_BLACKJACK WHERE ID_JOGO = ?",
            (idJogo,)
        )
        return self.__formatar()
    
    def consultaJogador(self, idJogador: str):
        self.__cursor.execute(
            "SELECT ID, ID_JOGO, NOME, VALOR_MAO FROM JOGADOR_BLACKJACK WHERE ID = ?",
            (idJogador,)
        )
        return self.__formatar()
    
    def createNovoJogo(self, jogo: BlackjackModel):
        self.__cursor.execute(
            "INSERT INTO BLACKJACK (ID, JOGADOR_HOST, VALOR_APOSTA) VALUES (?, ?, ?)",
            (jogo.getId(), jogo.getIdJogador(), jogo.getValorAposta())
        )
        self.__conn.commit()
        return self.consultarJogo(jogo.getId())

    def atualizarValorAposta(self, idJogo: str, valorAposta: float):
        self.__cursor.execute(
            "UPDATE BLACKJACK SET VALOR_APOSTA = ? WHERE ID = ?",
            (valorAposta, idJogo)
        )
        self.__conn.commit()
        return self.consultarJogo(idJogo)
    
    def createJogador(self, idJogo: str, jogador: JogadorBlackjackModel):
        self.__cursor.execute(
            "INSERT INTO JOGADOR_BLACKJACK (ID_JOGO, NOME) VALUES (?, ?)",
            (idJogo, jogador.getNome())
        )
        self.__conn.commit()
        
    def deleteJogo(self, idJogo: str):
        self.__cursor.execute(
            "DELETE FROM BLACKJACK WHERE ID = ?",
            (idJogo,)
        )
        self.__conn.commit()
    
    def __formatar(self):
        headers = [desc[0].lower() for desc in self.__cursor.description]
        return [dict(zip(headers, row)) for row in self.__cursor.fetchall()]
