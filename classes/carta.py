

class Carta:
    def __init__(self, suit, rank, valor):
        self.__suit = suit
        self.__rank = rank
        self.__valor = valor
        
    @classmethod
    def newCarta(cls, suit, rank, valor):
        return cls(suit, rank, valor)

    def getSuit(self):
        return self.__suit

    def setSuit(self, suit):
        self.__suit = suit

    def getRank(self):
        return self.__rank

    def setRank(self, rank):
        self.__rank = rank

    def getValor(self):
        return self.__valor

    def setValor(self, valor):
        self.__valor = valor