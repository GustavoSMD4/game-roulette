import uuid

class BlackjackModel:
    def __init__(self, id: str, idJogadorHost: str):
        self.__id = id
        self.__idJogadorHost = idJogadorHost
        
    @classmethod
    def newBlackjackModel(cls, req: dict = None):
        if req is None:
            return cls(str(uuid.uuid4()), None)
        
        id = req.get("id") or str(uuid.uuid4())
        idJogadorHost = req.get("idJogadorHost") or req.get("id_jogador_host") or req.get("jogador_host")
        
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
