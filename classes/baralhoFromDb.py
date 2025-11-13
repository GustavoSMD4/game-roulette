import random
import sqlite3
from classes.carta import Carta
from server.carta.repository.cartaRepo import CartaRepo

class BaralhoDb:
    def __init__(self):
        self.__cartas: list[Carta] = []

    @classmethod
    def newBaralhoFromDB(cls):
        baralho = cls()

        # Conecta ao banco
        conn = sqlite3.connect("server/database/database.db", check_same_thread=False)
        cursor = conn.cursor()

        cartas = CartaRepo.newRepo().consultarTodos()

        # Cria objetos Carta e adiciona ao baralho
        for rank, suit, valor, nomeImagem in linhas:
            baralho.__cartas.append(Carta.newCarta(suit, rank, valor, nomeImagem))

        conn.close()

        # Embaralha as cartas
        random.shuffle(baralho.__cartas)
        return baralho

    def deal(self):
        return self.__cartas.pop() if self.__cartas else None

    def getCartas(self):
        return self.__cartas

    def setCartas(self, cartas):
        self.__cartas = cartas
