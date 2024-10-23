
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

    def getNomeJogador(self):
        return self.__nomeJogador

    def setNomeJogador(self, nomeJogador):
        self.__nomeJogador = nomeJogador

    def addCard(self, carta):
        self.__cartas.append(carta)

    def isDealer(self):
        return self.__dealer

    def setDealer(self, dealer):
        self.__dealer = dealer
        
