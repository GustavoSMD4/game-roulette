from typing import Dict, List
from roulette import Roulette

roleta = Roulette.newRoulette()

resultados = {"won": {"times": 0, "amount": 0}, "lost": {"times": 0, "amount": 0}}
qtdeSim = 1000000
valorAposta = 100

for i in range(0, qtdeSim):
    result = roleta.playColor("black", valorAposta)
    
    if result.get("message") == "You won":
        resultados["won"]["times"] += 1  
        resultados["won"]["amount"] += result.get("amount") - valorAposta 
    else:
        resultados["lost"]["times"] += 1 
        resultados["lost"]["amount"] += result.get("amount")
        
print(resultados, resultados["won"]["amount"] - resultados["lost"]["amount"])
        
