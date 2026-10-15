from classes.jogador import Jogador


class MaoBlackjack:
    """Uma mão do jogador (o jogo pode ter várias quando há split)."""

    def __init__(self, indice: int = 0, valorAposta: float = 0, nomeJogador: str = None):
        self.__indice: int = indice
        self.__valorAposta: float = valorAposta
        self.__jogador: Jogador = Jogador.newJogador(None, nomeJogador)
        self.__encerrada: bool = False

    @classmethod
    def newMao(cls, req: dict = None):
        if req is None:
            return cls()

        return cls(
            int(req.get("indice") or 0),
            float(req.get("valor_aposta") or req.get("valorAposta") or 0),
            req.get("nome") or req.get("nome_jogador")
        )

    def getIndice(self) -> int:
        return self.__indice

    def setIndice(self, indice: int):
        self.__indice = indice

    def getValorAposta(self) -> float:
        return self.__valorAposta

    def setValorAposta(self, valorAposta: float):
        self.__valorAposta = valorAposta

    def getJogador(self) -> Jogador:
        return self.__jogador

    def getNome(self) -> str:
        return self.__jogador.getNomeJogador()

    def getCartas(self) -> list:
        return self.__jogador.getCards()

    def getValorMao(self) -> int:
        return self.__jogador.getValorMao()

    def addCard(self, carta):
        self.__jogador.addCard(carta)

    def removerUltimaCarta(self):
        return self.__jogador.removerUltimaCarta()

    def isEncerrada(self) -> bool:
        return self.__encerrada

    def encerrar(self):
        self.__encerrada = True

    def getDict(self) -> dict:
        return {
            "indice": self.__indice,
            "nome": self.getNome(),
            "valorMao": self.getValorMao(),
            "valorAposta": self.__valorAposta,
            "encerrada": self.__encerrada,
            "cartas": [carta.getDict() for carta in self.getCartas()]
        }
