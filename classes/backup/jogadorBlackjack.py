
from classes.carta import Carta


class JogadorBlackjack:
    def __init__(self, nomeJogador=None, dealer=False):
        self.__nomeJogador = nomeJogador
        self.__cartas: list[Carta] = []
        self.__dealer = False
        
    @classmethod
    def newJogador(cls):
        return cls()
    
    def printCards(self):
        for carta in self.__cartas:
            print(carta.getRank(), carta.getSuit())
            
    def printMao(self):
        print(f"Cartas de {self.__nomeJogador}")
        self.printCards()
        print(f"{self.__nomeJogador} tem {self.getValorMao()}")
    
    def getValorMao(self):
        valor = 0
        aces = 0
        
        for carta in self.__cartas:
            valor += carta.getValor()
            if carta.getValor() == 11:
                aces += 1
                
            while valor > 21 and aces > 0:
                valor -= 10
                aces -= 1
            
        return valor

    def getNomeJogador(self):
        return self.__nomeJogador

    def setNomeJogador(self, nomeJogador: str):
        self.__nomeJogador = nomeJogador

    def addCard(self, carta):
        self.__cartas.append(carta)

    def isDealer(self):
        return self.__dealer

    def setDealer(self, dealer: bool):
        self.__dealer = dealer
        
