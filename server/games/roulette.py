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
    
    def odds(self, type: Literal["number", "color"], item: Literal["red", "black"] | Literal[0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36]):
        pass
    
    def playColor(self, colorBet: Literal["red", "black"], betAmount: float):
        if colorBet != "red" and colorBet != "black":
            raise Exception("Not a valid color: only red or black")
        
        if not isinstance(betAmount, float):
            try:
                betAmount = float(betAmount)
            except:
                raise Exception("Error trying to convert the bet amount to float!")
        
        draw = self.__draw()
        result = draw.get("result")
        randomNumber = draw.get("randomNumber")
        
        return {
            "message": "You won" if result == colorBet else "You lost",
            "amount": (betAmount * 2) if result == colorBet else betAmount,
            "result": f"{result} {randomNumber}"
        }
        
    def playNumber(self, 
                   numberBet: Literal[0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36],
                   betAmount: float):
        
        if not isinstance(numberBet, int):
            try:
                numberBet = int(numberBet)
            except:
                raise Exception("Error trying to convert number to int!")
        
        if numberBet not in range(0, 37):
            raise Exception(f"Invalid number {numberBet}: select between 0-36")
        
        if not isinstance(betAmount, float):
            try:
                betAmount = float(betAmount)
            except:
                raise Exception("Error trying to convert the bet amount to float!")
            
        draw = self.__draw()
        result = draw.get("result")
        randomNumber = draw.get("randomNumber")
        
        return {
            "message": "You won" if numberBet == randomNumber else "You lost",
            "amount": (betAmount * 36) if numberBet == randomNumber else betAmount,
            "result": f"{result} {randomNumber}"
        }
        
        
    def __draw(self):
        randomNumber = random.randint(0, 36)
        result = self.__VALUES.get(randomNumber)
        
        return {"result": result, "randomNumber": randomNumber}
        
    
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
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        