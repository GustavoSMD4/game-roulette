class ResultadoBlackjack:
    def __init__(self):
        self.__id: int = None
        self.__idJogo: str = None
        self.__idJogador: str = None
        self.__indiceMao: int = 0
        self.__valorAposta: float = None
        self.__resultado: str = None
        self.__valorJogador: int = None
        self.__valorDealer: int = None
        self.__valorRecebido: float = None
        self.__lucro: float = None
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
        obj.setValorAposta(req.get('valor_aposta') or req.get('valorAposta'))
        obj.setResultado(req.get('resultado'))
        obj.setValorJogador(req.get('valor_jogador') or req.get('valorJogador'))
        obj.setValorDealer(req.get('valor_dealer') or req.get('valorDealer'))
        obj.setValorRecebido(req.get('valor_recebido') or req.get('valorRecebido'))
        obj.setLucro(req.get('lucro'))
        obj.setDataHora(req.get('data_hora') or req.get('dataHora'))
        return obj

    def getId(self) -> int:
        return self.__id

    def setId(self, id) -> None:
        self.__id = id

    def getIdJogador(self) -> str:
        return self.__idJogador

    def setIdJogador(self, idJogador: str) -> None:
        self.__idJogador = str(idJogador).strip() if idJogador else None

    def getIdJogo(self) -> str:
        return self.__idJogo

    def setIdJogo(self, idJogo: str) -> None:
        self.__idJogo = str(idJogo).strip() if idJogo else None

    def getIndiceMao(self) -> int:
        return self.__indiceMao

    def setIndiceMao(self, indiceMao) -> None:
        try:
            self.__indiceMao = int(indiceMao)
        except (TypeError, ValueError):
            self.__indiceMao = 0

    def getValorAposta(self) -> float:
        return self.__valorAposta

    def setValorAposta(self, valorAposta: float) -> None:
        try:
            self.__valorAposta = float(valorAposta)
        except (TypeError, ValueError):
            raise Exception("Valor Aposta precisa ser número")

    def getResultado(self) -> str:
        return self.__resultado

    def setResultado(self, resultado: str) -> None:
        self.__resultado = str(resultado).strip() if resultado else None

    def getValorJogador(self) -> int:
        return self.__valorJogador

    def setValorJogador(self, valorJogador: int) -> None:
        try:
            self.__valorJogador = int(valorJogador)
        except (TypeError, ValueError):
            self.__valorJogador = 0

    def getValorDealer(self) -> int:
        return self.__valorDealer

    def setValorDealer(self, valorDealer: int) -> None:
        try:
            self.__valorDealer = int(valorDealer)
        except (TypeError, ValueError):
            self.__valorDealer = 0

    def getValorRecebido(self) -> float:
        return self.__valorRecebido

    def setValorRecebido(self, valorRecebido: float) -> None:
        try:
            self.__valorRecebido = float(valorRecebido)
        except (TypeError, ValueError):
            self.__valorRecebido = 0.0

    def getLucro(self) -> float:
        return self.__lucro

    def setLucro(self, lucro: float) -> None:
        try:
            self.__lucro = float(lucro)
        except (TypeError, ValueError):
            self.__lucro = 0.0

    def getDataHora(self) -> str:
        return self.__dataHora

    def setDataHora(self, dataHora: str) -> None:
        self.__dataHora = str(dataHora).strip() if dataHora else None

    def getDict(self) -> dict:
        return {
            'id': self.getId(),
            'idJogo': self.getIdJogo(),
            'idJogador': self.getIdJogador(),
            'valorAposta': self.getValorAposta(),
            'resultado': self.getResultado(),
            'valorJogador': self.getValorJogador(),
            'valorDealer': self.getValorDealer(),
            'valorRecebido': self.getValorRecebido(),
            'lucro': self.getLucro(),
            'dataHora': self.getDataHora()
        }
