import uuid


class BlackjackModel:
    def __init__(self, id: str, jogadorVez: str):
        self.__id = id
        self.__jogadorVez = jogadorVez
        
    @classmethod
    def newBlackjackModel(cls, id = None, jogadorVez = False):
        if id is None:
            id = str(uuid.uuid4())
        
        return cls(id, jogadorVez)
    
    def getDict(self):
        return {
            "id": self.__id,
            "jogadorVez": self.__jogadorVez
        }
    
    def getId(self):
        return self.__id
    
    def getJogadorVez(self):
        return self.__jogadorVez
    
    def setJogadorVez(self, idJogador):
        self.__jogadorVez = idJogador