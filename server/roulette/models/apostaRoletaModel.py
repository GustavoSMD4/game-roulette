from utils import paraBrasiliaData


class ApostaRoleta:
    """Uma aposta feita por um jogador na mesa compartilhada."""

    def __init__(self):
        self.__id: int = None
        self.__idRodada: int = None
        self.__idJogador: str = None
        self.__nome: str = None
        self.__aposta: str = None
        self.__tipo: str = None
        self.__valorAposta: float = None
        self.__ganhou: int = None
        self.__valorRecebido: float = None
        self.__lucro: float = None
        self.__dataHora = None

    @classmethod
    def newModel(cls, req: dict = None):
        if req is None:
            return cls()

        obj = cls()
        obj.setId(req.get('id'))
        obj.setIdRodada(req.get('id_rodada') or req.get('idRodada'))
        obj.setIdJogador(req.get('id_jogador') or req.get('idJogador'))
        obj.setNome(req.get('nome'))
        obj.setAposta(req.get('aposta'))
        obj.setTipo(req.get('tipo'))
        obj.setValorAposta(req.get('valor_aposta') or req.get('valorAposta'))
        obj.setGanhou(req.get('ganhou'))
        obj.setValorRecebido(req.get('valor_recebido') or req.get('valorRecebido'))
        obj.setLucro(req.get('lucro'))
        obj.setDataHora(req.get('data_hora') or req.get('dataHora'))
        return obj

    def getId(self) -> int:
        return self.__id

    def setId(self, id) -> None:
        try:
            self.__id = int(id)
        except (TypeError, ValueError):
            self.__id = None

    def getIdRodada(self):
        return self.__idRodada

    def setIdRodada(self, idRodada) -> None:
        try:
            self.__idRodada = int(idRodada)
        except (TypeError, ValueError):
            self.__idRodada = None

    def getIdJogador(self):
        return self.__idJogador

    def setIdJogador(self, idJogador) -> None:
        self.__idJogador = str(idJogador).strip() if idJogador is not None else None

    def getNome(self) -> str:
        return self.__nome

    def setNome(self, nome) -> None:
        self.__nome = str(nome).strip() if nome else None

    def getAposta(self) -> str:
        return self.__aposta

    def setAposta(self, aposta) -> None:
        self.__aposta = str(aposta).strip().lower() if aposta is not None else None

    def getTipo(self) -> str:
        return self.__tipo

    def setTipo(self, tipo) -> None:
        self.__tipo = str(tipo).strip().lower() if tipo else None

    def getValorAposta(self) -> float:
        return self.__valorAposta

    def setValorAposta(self, valorAposta) -> None:
        try:
            self.__valorAposta = float(valorAposta)
        except (TypeError, ValueError):
            raise Exception("Valor da aposta precisa ser um número")

    def getGanhou(self):
        return self.__ganhou

    def setGanhou(self, ganhou) -> None:
        try:
            self.__ganhou = int(ganhou)
        except (TypeError, ValueError):
            self.__ganhou = None

    def getValorRecebido(self) -> float:
        return self.__valorRecebido

    def setValorRecebido(self, valorRecebido) -> None:
        try:
            self.__valorRecebido = float(valorRecebido)
        except (TypeError, ValueError):
            self.__valorRecebido = 0.0

    def getLucro(self) -> float:
        return self.__lucro

    def setLucro(self, lucro) -> None:
        try:
            self.__lucro = float(lucro)
        except (TypeError, ValueError):
            self.__lucro = 0.0

    def isPaga(self) -> bool:
        return self.__ganhou is not None

    def getDataHora(self):
        return self.__dataHora

    def setDataHora(self, dataHora) -> None:
        self.__dataHora = paraBrasiliaData(dataHora)

    def getDict(self) -> dict:
        return {
            'id': self.getId(),
            'idJogador': self.getIdJogador(),
            'nome': self.getNome(),
            'aposta': self.getAposta(),
            'tipo': self.getTipo(),
            'valorAposta': self.getValorAposta(),
            'ganhou': self.getGanhou(),
            'valorRecebido': self.getValorRecebido(),
            'lucro': self.getLucro()
        }
