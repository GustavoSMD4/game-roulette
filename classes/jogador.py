
from classes.carta import Carta


class Jogador:
    def __init__(self, idUsuario = None, nomeJogador=None, dealer=False):
        self.__idJogador = idUsuario
        self.__nomeJogador = nomeJogador
        self.__cartas: list[Carta] = []
        self.__valorAposta: float = None
        
    @classmethod
    def newJogador(cls, idUsuario = None, nomeUsuario = None):
        return cls(idUsuario, nomeUsuario)
    
    def getValorMao(self):
        return self.__valorDasCartas(self.__cartas)

    def getValoresParciais(self):
        """Valor da mão depois de cada carta, na ordem em que foram recebidas."""
        return [self.__valorDasCartas(self.__cartas[:indice]) for indice in range(1, len(self.__cartas) + 1)]

    def __valorDasCartas(self, cartas):
        valor = 0
        aces = 0
        
        for carta in cartas:
            valor += carta.getValor()
            if carta.getValor() == 11:
                aces += 1
                
            while valor > 21 and aces > 0:
                valor -= 10
                aces -= 1
            
        return valor
    
    def getId(self):
        return self.__idJogador
    
    def setId(self, id):
        self.__idJogador = id

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

    def removerUltimaCarta(self):
        return self.__cartas.pop() if self.__cartas else None
