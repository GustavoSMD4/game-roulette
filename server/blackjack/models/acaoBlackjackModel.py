class AcaoBlackjack:
    def __init__(self):
        self.__id: int = None
        self.__idJogo: str = None
        self.__idJogador: str = None
        self.__indiceMao: int = 0
        self.__acao: str = None
        self.__dono: str = None
        self.__carta: str = None
        self.__valorJogador: int = None
        self.__valorDealer: int = None
        self.__dataHora: str = None

    @classmethod
    def newModel(cls, req: dict = None):
        if req is None:
            return cls()

        obj = cls()
        obj.setId(req.get('id'))
        obj.setIdJogo(req.get('id_jogo') or req.get('idJogo'))
        obj.setIdJogador(req.get('id_jogador') or req.get('idJogador'))
        obj.setIndiceMao(req.get('indice_mao') or req.get('indiceMao'))
        obj.setAcao(req.get('acao'))
        obj.setDono(req.get('dono'))
        obj.setCarta(req.get('carta'))
        obj.setValorJogador(req.get('valor_jogador') or req.get('valorJogador'))
        obj.setValorDealer(req.get('valor_dealer') or req.get('valorDealer'))
        obj.setDataHora(req.get('data_hora') or req.get('dataHora'))
        return obj

    def getId(self) -> int:
        return self.__id

    def setId(self, id) -> None:
        self.__id = id

    def getIdJogo(self) -> str:
        return self.__idJogo

    def setIdJogo(self, idJogo: str) -> None:
        self.__idJogo = str(idJogo).strip() if idJogo else None

    def getIdJogador(self) -> str:
        return self.__idJogador

    def setIdJogador(self, idJogador) -> None:
        self.__idJogador = str(idJogador).strip() if idJogador is not None else None

    def getAcao(self) -> str:
        return self.__acao

    def setAcao(self, acao: str) -> None:
        self.__acao = str(acao).strip() if acao else None

    def getIndiceMao(self) -> int:
        return self.__indiceMao

    def setIndiceMao(self, indiceMao) -> None:
        try:
            self.__indiceMao = int(indiceMao)
        except (TypeError, ValueError):
            self.__indiceMao = 0

    def getDono(self) -> str:
        return self.__dono

    def setDono(self, dono: str) -> None:
        self.__dono = str(dono).strip() if dono else None

    def getCarta(self) -> str:
        return self.__carta

    def setCarta(self, carta: str) -> None:
        self.__carta = str(carta).strip() if carta else None

    def getValorJogador(self) -> int:
        return self.__valorJogador

    def setValorJogador(self, valorJogador) -> None:
        try:
            self.__valorJogador = int(valorJogador)
        except (TypeError, ValueError):
            self.__valorJogador = 0

    def getValorDealer(self) -> int:
        return self.__valorDealer

    def setValorDealer(self, valorDealer) -> None:
        try:
            self.__valorDealer = int(valorDealer)
        except (TypeError, ValueError):
            self.__valorDealer = 0

    def getDataHora(self) -> str:
        return self.__dataHora

    def setDataHora(self, dataHora: str) -> None:
        self.__dataHora = str(dataHora).strip() if dataHora else None

    def getDict(self) -> dict:
        return {
            'id': self.getId(),
            'idJogo': self.getIdJogo(),
            'idJogador': self.getIdJogador(),
            'indiceMao': self.getIndiceMao(),
            'acao': self.getAcao(),
            'dono': self.getDono(),
            'carta': self.getCarta(),
            'valorJogador': self.getValorJogador(),
            'valorDealer': self.getValorDealer(),
            'dataHora': self.getDataHora()
        }
