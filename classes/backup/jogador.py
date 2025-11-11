
from classes.carta import Carta


class Jogador:
    def __init__(self, nomeJogador=None, dealer=False):
        self.__nomeJogador = nomeJogador
        self.__cartas: list[Carta] = []
        self.__valorAposta: float = None
        
    @classmethod
    def newJogador(cls):
        return cls()
    
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
        
    def getValorAposta(self):
        return self.__valorAposta
    
    def setValorAposta(self, valor):
        self.__valorAposta = valor
        
    def getCards(self):
        return self.__cartas

    def addCard(self, carta):
        self.__cartas.append(carta)
