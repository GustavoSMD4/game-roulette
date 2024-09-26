from typing import Dict, List
from games.roulette import Roulette
import utils

def teste():
    roleta = Roulette.newRoulette()

    resultados = {"won": {"times": 0, "amount": 0}, "lost": {"times": 0, "amount": 0}}
    results = {"won": [], "amount": []}
    
    qtdeSim = 1000000
    valorAposta = 1000
    dinheiroInicial = 1000

    for i in range(0, qtdeSim):
        result = roleta.playNumber(11, valorAposta)

        if result.get("message") == "You won":
            resultados["won"]["amount"] += result.get("amount") - valorAposta
            resultados["won"]["times"] += 1
            
            results["won"].append(1)
            results["amount"].append(result.get("amount") - valorAposta)
            dinheiroInicial = dinheiroInicial + result.get("amount") - valorAposta
        else:
            resultados["lost"]["amount"] += result.get("amount")
            resultados["lost"]["times"] += 1
            
            results["won"].append(0) 
            results["amount"].append(result.get("amount"))
            dinheiroInicial = dinheiroInicial - result.get("amount")

    return resultados

resultados = teste()
print(resultados, utils.formatarReal(resultados.get("won")["amount"] - resultados.get("lost")["amount"]))
