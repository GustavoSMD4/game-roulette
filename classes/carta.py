class Carta:
    def __init__(self, id, suit, rank, valor, nomeImagem):
        self.__id: str = id
        self.__suit: str = suit
        self.__rank: str = rank
        self.__valor: int = valor
        self.__nomeImagem: str = nomeImagem
        
    @classmethod
    def newCarta(cls, req: dict):
        id = req.get("id")
        suit = req.get("suit")
        rank = req.get("rank")
        valor = req.get("valor")
        nomeImagem = req.get("nomeImagem") or req.get("nome_imagem")

        return cls(id, suit, rank, valor, nomeImagem)

    def getId(self):
        return self.__id

    def setId(self, id: str):
        self.__id = id

    def getSuit(self):
        return self.__suit

    def setSuit(self, suit):
        self.__suit = suit

    def getRank(self):
        return self.__rank

    def setRank(self, rank):
        self.__rank = rank

    def getValor(self):
        return self.__valor

    def setValor(self, valor):
        self.__valor = valor
        
    def getNomeImagem(self):
        return self.__nomeImagem
    
    def setNomeImagem(self, nomeImagem: str):
        self.__nomeImagem = nomeImagem