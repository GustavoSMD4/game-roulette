

class Carta:
    def __init__(self, suit, rank, valor, nomeImagem):
        self.__suit: str = suit
        self.__rank: str = rank
        self.__valor: int = valor
        self.__nomeImagem: str = nomeImagem
        
    @classmethod
    def newCarta(cls, suit, rank, valor, nomeImagem):
        return cls(suit, rank, valor, nomeImagem)

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
        
    def getNomeImagem(self):
        return self.__nomeImagem
    
    def setNomeImagem(self, nomeImagem: str):
        self.__nomeImagem = nomeImagem