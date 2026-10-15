import uuid

class BlackjackModel:
    def __init__(self, id: str, idJogadorHost: str, valorAposta: float = 0):
        self.__id = id
        self.__idJogadorHost = idJogadorHost
        self.__valorAposta = valorAposta
        
    @classmethod
    def newBlackjackModel(cls, req: dict = None):
        if req is None:
            return cls(str(uuid.uuid4()), None)
        
        id = req.get("id") or str(uuid.uuid4())
        idJogadorHost = req.get("idJogadorHost") or req.get("id_jogador_host") or req.get("jogador_host")
        valorAposta = req.get("valorAposta") or req.get("valor_aposta") or 0
        
        return cls(id, idJogadorHost, valorAposta)
    
    def getDict(self):
        return {
            "id": self.__id,
            "idJogadorHost": self.__idJogadorHost,
            "valorAposta": self.__valorAposta
        }
    
    def getId(self):
        return self.__id
    
    def getIdJogador(self):
        return self.__idJogadorHost
    
    def setIdJogador(self, idJogador):
        self.__idJogadorHost = idJogador

    def getValorAposta(self):
        return self.__valorAposta

    def setValorAposta(self, valorAposta):
        self.__valorAposta = valorAposta
