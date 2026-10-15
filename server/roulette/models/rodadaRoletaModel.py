from utils import paraBrasiliaData


class RodadaRoleta:
    """Uma rodada da mesa compartilhada: abre a janela de apostas, fecha, sorteia e paga."""

    def __init__(self):
        self.__id: int = None
        self.__idSessao: int = None
        self.__dataHoraInicio = None
        self.__dataHoraFechamento = None
        self.__numero: int = None
        self.__cor: str = None

    @classmethod
    def newModel(cls, req: dict = None):
        if req is None:
            return cls()

        obj = cls()
        obj.setId(req.get('id'))
        obj.setIdSessao(req.get('id_sessao') or req.get('idSessao'))
        obj.setDataHoraInicio(req.get('data_hora_inicio') or req.get('dataHoraInicio'))
        obj.setDataHoraFechamento(req.get('data_hora_fechamento') or req.get('dataHoraFechamento'))
        obj.setNumero(req.get('numero'))
        obj.setCor(req.get('cor'))
        return obj

    def getId(self) -> int:
        return self.__id

    def setId(self, id: int) -> None:
        try:
            self.__id = int(id)
        except (TypeError, ValueError):
            self.__id = None

    def getIdSessao(self):
        return self.__idSessao

    def setIdSessao(self, idSessao) -> None:
        try:
            self.__idSessao = int(idSessao)
        except (TypeError, ValueError):
            self.__idSessao = None

    def getDataHoraInicio(self):
        return self.__dataHoraInicio

    def setDataHoraInicio(self, dataHora) -> None:
        self.__dataHoraInicio = paraBrasiliaData(dataHora)

    def getDataHoraFechamento(self):
        return self.__dataHoraFechamento

    def setDataHoraFechamento(self, dataHora) -> None:
        self.__dataHoraFechamento = paraBrasiliaData(dataHora)

    def getNumero(self):
        return self.__numero

    def setNumero(self, numero) -> None:
        try:
            self.__numero = int(numero)
        except (TypeError, ValueError):
            self.__numero = None

    def getCor(self):
        return self.__cor

    def setCor(self, cor) -> None:
        self.__cor = str(cor).strip().lower() if cor else None

    def isSorteada(self) -> bool:
        return self.__numero is not None

    def getDict(self) -> dict:
        return {
            'idRodada': self.getId(),
            'numero': self.getNumero(),
            'cor': self.getCor(),
            'dataHoraInicio': self.__dataHoraInicio.strftime("%Y-%m-%d %H:%M:%S") if self.__dataHoraInicio else None,
            'dataHoraFechamento': self.__dataHoraFechamento.strftime("%Y-%m-%d %H:%M:%S") if self.__dataHoraFechamento else None
        }
