

from classes.baralho import Baralho
from classes.jogadorBlackjack import JogadorBlackjack


class Blackjack:
    def __init__(self, baralho: Baralho, jogadores: list[JogadorBlackjack], dealer: JogadorBlackjack) -> None:
        self.__baralho = baralho
        self.__jogadores = jogadores
        self.__dealer = dealer
        
    @classmethod
    def newBlackjack(cls, nomesJogadores: list[str]):
        baralho = Baralho.newBaralho(4)
        jogadores = []
        dealer = JogadorBlackjack.newJogador()
        dealer.setNomeJogador("Dealer")
        dealer.setDealer(True)
        
        for nome in nomesJogadores:
            jogador = JogadorBlackjack.newJogador()
            jogador.setNomeJogador(nome)
            jogadores.append(jogador)
        
        return cls(baralho, jogadores, dealer)
    
    def play(self):
        self.__dealer.addCard(self.__baralho.deal())
        
        for jogador in self.__jogadores:
            self.__dealer.printMao()
            jogador.addCard(self.__baralho.deal())
            jogador.addCard(self.__baralho.deal())
            jogador.printMao()
        
        
            