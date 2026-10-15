import json

from utils import paraBrasiliaData


class RodadaBlackjack:
    """Uma rodada da mesa ao vivo: fase, prazo e o estado completo da mesa em JSON."""

    def __init__(self):
        self.__id: int = None
        self.__idSala: int = None
        self.__numero: int = None
        self.__fase: str = None
        self.__dataHoraInicio = None
        self.__dataHoraFimFase = None
        self.__estado: dict = {}

    @classmethod
    def newModel(cls, req: dict = None):
        if req is None:
            return cls()

        obj = cls()
        obj.setId(req.get('id'))
        obj.setIdSala(req.get('id_sala') or req.get('idSala'))
        obj.setNumero(req.get('numero'))
        obj.setFase(req.get('fase'))
        obj.setDataHoraInicio(req.get('data_hora_inicio') or req.get('dataHoraInicio'))
        obj.setDataHoraFimFase(req.get('data_hora_fim_fase') or req.get('dataHoraFimFase'))
        obj.setEstado(req.get('estado'))
        return obj

    def getId(self) -> int:
        return self.__id

    def setId(self, id) -> None:
        try:
            self.__id = int(id)
        except (TypeError, ValueError):
            self.__id = None

    def getIdSala(self):
        return self.__idSala

    def setIdSala(self, idSala) -> None:
        try:
            self.__idSala = int(idSala)
        except (TypeError, ValueError):
            self.__idSala = None

    def getNumero(self):
        return self.__numero

    def setNumero(self, numero) -> None:
        try:
            self.__numero = int(numero)
        except (TypeError, ValueError):
            self.__numero = None

    def getFase(self) -> str:
        return self.__fase

    def setFase(self, fase) -> None:
        self.__fase = str(fase).strip() if fase else None

    def getDataHoraInicio(self):
        return self.__dataHoraInicio

    def setDataHoraInicio(self, dataHora) -> None:
        self.__dataHoraInicio = paraBrasiliaData(dataHora)

    def getDataHoraFimFase(self):
        return self.__dataHoraFimFase

    def setDataHoraFimFase(self, dataHora) -> None:
        self.__dataHoraFimFase = paraBrasiliaData(dataHora)

    def getEstado(self) -> dict:
        return self.__estado or {}

    def setEstado(self, estado) -> None:
        if not estado:
            self.__estado = {}
            return

        if isinstance(estado, dict):
            self.__estado = estado
            return

        try:
            self.__estado = json.loads(estado)
        except (TypeError, ValueError):
            self.__estado = {}

    def setEstadoDict(self, estado: dict) -> None:
        self.__estado = estado or {}

    def segundosRestantes(self, agora) -> int:
        if self.__dataHoraFimFase is None:
            return 0

        return max(0, int((self.__dataHoraFimFase - agora).total_seconds() + 0.999))
