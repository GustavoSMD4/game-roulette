import random
import sqlite3
from classes.carta import Carta
from server.carta.repository.cartaRepo import CartaRepo

class BaralhoDb:
    def __init__(self):
        self.__cartas: list[Carta] = []

    @classmethod
    def newBaralhoFromDb(cls, qtdeBaralhos: int = 4):
        baralho = cls()
        cartasBase = CartaRepo.newRepo().consultarTodos()
        baralhoCompleto = cartasBase * qtdeBaralhos
        baralho.setCartas(baralhoCompleto)
        random.shuffle(baralho.getCartas())
        return baralho
    
    def deal(self, idCarta: str = None):
        if idCarta is None:
            return self.__cartas.pop() if self.__cartas else None
        
        for i, carta in enumerate(self.__cartas):
            if carta.getId() == idCarta:
                return self.__cartas.pop(i)
        
        return None

    def getCartas(self):
        return self.__cartas

    def setCartas(self, cartas):
        self.__cartas = cartas
