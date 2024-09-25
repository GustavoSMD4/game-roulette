
import random
from typing import Literal


class Roulette:
    def __init__(self) -> None:
        self.__VALUES = {}
    
    @classmethod
    def newRoulette(cls):
        roulette = cls()
        roulette.__init()
        return roulette
    
    def getValues(self):
        return self.__VALUES
    
    def playColor(self, colorBet: Literal["red", "black"], betAmount: float):
        if not isinstance(betAmount, float):
            try:
                betAmount = float(betAmount)
            except:
                raise Exception("Error trying to convert the bet amount to float!")
        
        numeroAleatorio = random.randint(0, 36)
        result = self.__VALUES.get(numeroAleatorio)
        
        return {
            "message": "You won" if result == colorBet else "You lost",
            "amount": (betAmount * 2) if result == colorBet else betAmount,
            "result": f"{result} {numeroAleatorio}"
        }
        
    
    def __init(self):
        self.__initValues()
    
     
    def __initValues(self):
        reds = [1, 3, 5, 7, 9, 12, 14, 16, 18, 19, 21, 23, 25, 27, 30, 32, 34, 36]
        blacks = [2, 4, 6, 8, 10, 11, 13, 15, 17, 20, 22, 24, 26, 28, 29, 31, 33, 35]

        for number in reds:
            self.__VALUES[number] = "red"

        for number in blacks:
            self.__VALUES[number] = "black"

        self.__VALUES[0] = "green"
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        