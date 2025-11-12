class ResultadoRoleta:
    def __init__(self):
        self.__idJogador: str = None
        self.__apostaJogador: str = None
        self.__valorAposta: float = None
        self.__resultado: str = None
        self.__valorResultado: float = None
        self.__ganhou: int = None
        self.__dataHora: str = None

    @classmethod
    def newModel(cls, req: dict = None):
        if req is None:
            return cls()

        obj = cls()
        obj.setIdJogador(req.get('id_jogador') or req.get('idJogador'))
        obj.setApostaJogador(req.get('aposta_jogador') or req.get('apostaJogador'))
        obj.setValorAposta(req.get('valor_aposta') or req.get('valorAposta'))
        obj.setResultado(req.get('resultado'))
        obj.setValorResultado(req.get('valor_resultado') or req.get('valorResultado'))
        obj.setGanhou(req.get('ganhou'))
        obj.setDataHora(req.get('data_hora') or req.get('dataHora'))
        return obj

    def getIdJogador(self) -> str:
        return self.__idJogador

    def setIdJogador(self, idJogador: str) -> None:
        self.__idJogador = str(idJogador).strip() if idJogador else None

    def getApostaJogador(self) -> str:
        return self.__apostaJogador

    def setApostaJogador(self, apostaJogador: str) -> None:
        self.__apostaJogador = str(apostaJogador).strip() if apostaJogador else None

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

    def getValorResultado(self) -> float:
        return self.__valorResultado

    def setValorResultado(self, valorResultado: float) -> None:
        try:
            self.__valorResultado = float(valorResultado)
        except (TypeError, ValueError):
            self.__valorResultado = None

    def getGanhou(self) -> int:
        return self.__ganhou

    def setGanhou(self, ganhou: int) -> None:
        try:
            self.__ganhou = int(ganhou)
        except (TypeError, ValueError):
            self.__ganhou = 0

    def getDataHora(self) -> str:
        return self.__dataHora

    def setDataHora(self, dataHora: str) -> None:
        self.__dataHora = str(dataHora).strip() if dataHora else None

    def getDict(self) -> dict:
        return {
            'idJogador': self.getIdJogador(),
            'apostaJogador': self.getApostaJogador(),
            'valorAposta': self.getValorAposta(),
            'resultado': self.getResultado(),
            'valorResultado': self.getValorResultado(),
            'ganhou': self.getGanhou(),
            'dataHora': self.getDataHora()
        }
