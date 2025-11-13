class CartaJogadorBlackjack:
    def __init__(self, id: str = None, idJogo: str = None, idJogador: str = None, idCarta: str = None):
        self.__id: str = id
        self.__idJogo: str = idJogo
        self.__idJogador: str = idJogador
        self.__idCarta: str = idCarta

    @classmethod
    def newModel(cls, req: dict = None):
        if req is None:
            return cls()
         
        return cls(
            req.get('id'),
            req.get('id_jogo') or req.get('idJogo'),
            req.get('id_jogador') or req.get('idJogador'),
            req.get('id_carta') or req.get('idCarta')
        )

    def getId(self) -> str:
        return self.__id

    def setId(self, id: str):
        self.__id = id

    def getIdJogo(self) -> str:
        return self.__idJogo

    def setIdJogo(self, idJogo: str):
        self.__idJogo = idJogo

    def getIdJogador(self) -> str:
        return self.__idJogador

    def setIdJogador(self, idJogador: str):
        self.__idJogador = idJogador

    def getIdCarta(self) -> str:
        return self.__idCarta

    def setIdCarta(self, idCarta: str):
        self.__idCarta = idCarta
