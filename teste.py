from typing import Dict, List
from games.roulette import Roulette

def teste():
    roleta = Roulette.newRoulette()

    resultados = {"won": {"times": 0, "amount": 0}, "lost": {"times": 0, "amount": 0}}
    results = {"won": [], "amount": []}
    
    qtdeSim = 1000000
    valorAposta = 100
    dinheiroInicial = 1000

    for i in range(0, qtdeSim):
        result = roleta.playColor("black", valorAposta)

        if result.get("message") == "You won":
            results["won"].append(1)
            results["amount"].append(result.get("amount") - valorAposta)
            dinheiroInicial = dinheiroInicial + result.get("amount") - valorAposta
        else:
            results["won"].append(0) 
            results["amount"].append(result.get("amount"))
            dinheiroInicial = dinheiroInicial - result.get("amount")

    return results
        
