from utils import paraBrasiliaData

# Modos de mesa: 1x1 (2 jogadores) ou 2x2 (4 jogadores, parceiros frente a frente)
MODOS = {"1x1": 2, "2x2": 4}


class SalaTruco:
    """Sala privada de truco: código do link de convite, modo da mesa e prazo de validade."""

    def __init__(self):
        self.__id: int = None
        self.__codigo: str = None
        self.__nome: str = None
        self.__modo: str = "2x2"
        self.__idCriador: str = None
        self.__dataHoraCriacao = None
        self.__dataHoraExpiracao = None

    @classmethod
    def newModel(cls, req: dict = None):
        if req is None:
            return cls()

        obj = cls()
        obj.setId(req.get('id'))
        obj.setCodigo(req.get('codigo'))
        obj.setNome(req.get('nome'))
        obj.setModo(req.get('modo'))
        obj.setIdCriador(req.get('id_criador') or req.get('idCriador'))
        obj.setDataHoraCriacao(req.get('data_hora_criacao') or req.get('dataHoraCriacao'))
        obj.setDataHoraExpiracao(req.get('data_hora_expiracao') or req.get('dataHoraExpiracao'))
        return obj

    def getId(self) -> int:
        return self.__id

    def setId(self, id) -> None:
        try:
            self.__id = int(id)
        except (TypeError, ValueError):
            self.__id = None

    def getCodigo(self) -> str:
        return self.__codigo

    def setCodigo(self, codigo) -> None:
        self.__codigo = str(codigo).strip().upper() if codigo else None

    def getNome(self) -> str:
        return self.__nome

    def setNome(self, nome) -> None:
        self.__nome = str(nome).strip() if nome else None

    def getModo(self) -> str:
        return self.__modo

    def setModo(self, modo) -> None:
        texto = str(modo or "").strip().lower()
        self.__modo = texto if texto in MODOS else "2x2"

    def getJogadoresPorMesa(self) -> int:
        return MODOS.get(self.__modo, 4)

    def getIdCriador(self):
        return self.__idCriador

    def setIdCriador(self, idCriador) -> None:
        self.__idCriador = str(idCriador).strip() if idCriador is not None else None

    def getDataHoraCriacao(self):
        return self.__dataHoraCriacao

    def setDataHoraCriacao(self, dataHora) -> None:
        self.__dataHoraCriacao = paraBrasiliaData(dataHora)

    def getDataHoraExpiracao(self):
        return self.__dataHoraExpiracao

    def setDataHoraExpiracao(self, dataHora) -> None:
        self.__dataHoraExpiracao = paraBrasiliaData(dataHora)

    def isExpirada(self, agora) -> bool:
        return self.__dataHoraExpiracao is not None and agora >= self.__dataHoraExpiracao

    def segundosRestantes(self, agora) -> int:
        if self.__dataHoraExpiracao is None:
            return 0

        return max(0, int((self.__dataHoraExpiracao - agora).total_seconds() + 0.999))

    def getDict(self) -> dict:
        return {
            'idSala': self.getId(),
            'codigo': self.getCodigo(),
            'nome': self.getNome(),
            'modo': self.getModo(),
            'jogadoresPorMesa': self.getJogadoresPorMesa(),
            'dataHoraExpiracao': self.__dataHoraExpiracao.strftime("%Y-%m-%d %H:%M:%S") if self.__dataHoraExpiracao else None
        }
