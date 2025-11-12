import requests
import sys
import os
sys.path.append(os.getcwd())
from server.roulette.service.rouletteService import RouletteService


class RoletaPlayTeste:
    def __init__(self):
        self.idUsuario = 1
        self.nomeUsuario = "teste"
        self.bet = "red"
        self.betAmount = 10
        self.URL = "http://localhost:5000"
        
    def playEndpoint(self, idUsuario: int = None, nomeUsuario: str = None, bet: str | int = None, betAmount: int = None):
        if idUsuario is not None:
            self.idUsuario = idUsuario
        if nomeUsuario is not None:
            self.nomeUsuario = nomeUsuario
        if bet is not None:
            self.bet = bet
        if betAmount is not None:
            self.betAmount = betAmount
        
        response = requests.post(self.URL + "/roulette/play", json=dict(
            idUsuario=self.idUsuario,
            nomeUsuario=self.nomeUsuario,
            bet=self.bet,
            bet_amount=self.betAmount,
        ))
        
        print(response.text)
        return response
    
    def jogarTeste(self):
        roletaService = RouletteService.newService()
        testes = 1000000
        i = 1
        
        while i < testes:
            roletaService.play(dict(idUsuario=755962235066646569, nomeUsuario="gustavogomes6448", bet="red", bet_amount=1))
            i += 1
        
        print("Acabou")
            
RoletaPlayTeste().jogarTeste()

    

