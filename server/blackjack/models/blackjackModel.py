import uuid


class BlackjackModel:
    def __init__(self, id: str, idJogadorHost: str):
        self.__id = id
        self.__idJogadorHost = idJogadorHost
        
    @classmethod
    def newBlackjackModel(cls, id = None, idJogadorHost = False):
        if id is None:
            id = str(uuid.uuid4())
        
        return cls(id, idJogadorHost)
    
    def getDict(self):
        return {
            "id": self.__id,
            "idJogadorHost": self.__idJogadorHost
        }
    
    def getId(self):
        return self.__id
    
    def getIdJogador(self):
        return self.__idJogadorHost
    
    def setIdJogador(self, idJogador):
        self.__idJogadorHost = idJogador