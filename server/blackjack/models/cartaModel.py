

import uuid


class CartaJogadorBlackjackModel:
    def __init__(self, id, idJogo, idJogador, rank, suit, valor):
        self.__id = id
        self.__idJogo = idJogo
        self.__idJogador = idJogador
        self.__rank = rank
        self.__suit = suit
        self.__valor = valor
        
   
    @classmethod
    def newCartaJogadorBlackjack(cls, id, idJogo, idJogador, rank, suit, valor):
        if id is None:
            id = str(uuid.uuid4())
            
        return cls(id, idJogo, idJogador, rank, suit, valor)

    def getDict(self):
        return {
            "id": self.__id,
            "idJogo": self.__idJogo,
            "idJogador": self.__idJogador,
            "rank": self.__rank,
            "suit": self.__suit,
            "valor": self.__valor
        }

    def getId(self):
        return self.__id

    def setId(self, id):
        self.__id = id

    def getIdJogo(self):
        return self.__idJogo

    def setIdJogo(self, idJogo):
        self.__idJogo = idJogo

    def getIdJogador(self):
        return self.__idJogador

    def setIdJogador(self, idJogador):
        self.__idJogador = idJogador

    def getRank(self):
        return self.__rank

    def setRank(self, rank):
        self.__rank = rank

    def getSuit(self):
        return self.__suit

    def setSuit(self, suit):
        self.__suit = suit

    def getValor(self):
        return self.__valor

    def setValor(self, valor):
        self.__valor = valor
