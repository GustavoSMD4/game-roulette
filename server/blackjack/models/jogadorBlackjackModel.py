

import uuid


class JogadorBlackjackModel:
    def __init__(self, id, nome, valorMao):
        self.__id = id
        self.__nome = nome
        self.__valorMao = valorMao

    @classmethod
    def newJogadorBlackjack(cls, nome, id = None, valorMao = 0):    
        return cls(id, nome, valorMao)

    def getDict(self):
        return {
            "id": self.__id,
            "nome": self.__nome,
            "valorMao": self.__valorMao
        }

    def getId(self):
        return self.__id

    def setId(self, id):
        self.__id = id

    def getNome(self):
        return self.__nome

    def setNome(self, nome):
        self.__nome = nome

    def getValorMao(self):
        return self.__valorMao

    def setValorMao(self, valorMao):
        self.__valorMao = valorMao
