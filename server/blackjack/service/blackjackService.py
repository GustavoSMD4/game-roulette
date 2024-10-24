

from server.blackjack.models.blackjackModel import BlackjackModel
from server.blackjack.models.jogadorBlackjackModel import JogadorBlackjackModel
from server.blackjack.repository.blackjackRepo import BlackjackRepo


class BlackjackService:
    def __init__(self, repository: BlackjackRepo):
        self.__repository = repository
        
    @classmethod
    def blackjackService(cls):
        return cls(BlackjackRepo.newBlackjackRepo())
    
    def createNovoJogoBlackjack(self, req: dict):
        jogadores = req.get("jogadores")
        novoJogo = BlackjackModel.newBlackjackModel()
        self.__repository.createNovoJogo(novoJogo)
        [self.__repository.createJogador(novoJogo.getId(), JogadorBlackjackModel.newJogadorBlackjack(nome)) for nome in jogadores]

        return self.__repository.consultarJogadores(novoJogo.getId())