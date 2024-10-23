
import random

from classes.carta import Carta

class Baralho:
    def __init__(self):
        self.__cartas: list[Carta] = []
        
    @classmethod
    def newBaralho(cls, qtdeBaralhos):
        baralho = cls()
        suits = ["Ouros", "Copas", "Espadas", "Paus"]
        ranks = ["2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K", "A"]
        
        for x in range(qtdeBaralhos):
            for suit in suits:
                for i, rank in enumerate(ranks):
                    valorCarta = i + 2 if i < 8 else 10 if i < 12 else 11
                    baralho.__cartas.append(Carta.newCarta(suit, rank, valorCarta))
        
        random.shuffle(baralho.__cartas)
        return baralho

    def deal(self):
        return self.__cartas.pop()              

    def getCartas(self):
        return self.__cartas

    def setCartas(self, cartas):
        self.__cartas = cartas
        
