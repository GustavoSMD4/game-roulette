
import random

from classes.carta import Carta

class Baralho:
    def __init__(self):
        self.__cartas: list[Carta] = []
        
    @classmethod
    def newBaralho(cls, qtdeBaralhos):
        baralho = cls()
        suits = ["Diamonds", "Hearts", "Spades", "Clubs"]
        ranks = ["2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K", "A"]
        
        for x in range(qtdeBaralhos):
            for suit in suits:
                for i, rank in enumerate(ranks):
                    valorCarta = i + 2 if i < 8 else 10 if i < 12 else 11
                    nomeImagem = f"{baralho.__getNomeRank(rank)}_of_{suit.lower()}.png"
                    baralho.__cartas.append(Carta.newCarta(suit, rank, valorCarta, nomeImagem))
        
        random.shuffle(baralho.__cartas)
        return baralho
    
    def deal(self):
        return self.__cartas.pop()              

    def getCartas(self):
        return self.__cartas

    def setCartas(self, cartas):
        self.__cartas = cartas
        
    @staticmethod
    def __getNomeRank(rank):
        if rank == "A":
            return "ace"
        
        if rank == "K":
            return "king"
        
        if rank == "Q":
            return "queen"
        
        if rank == "J":
             return "jack"
         
        return rank

        
