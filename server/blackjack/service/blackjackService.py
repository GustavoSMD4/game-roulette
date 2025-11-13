from classes.blackjack import Blackjack
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
        idUsuario = req.get("idUsuario")
        nomeUsuario = req.get("nomeUsuario")        
        return Blackjack([JogadorBlackjackModel.newJogadorBlackjack(nome=nomeUsuario, id=idUsuario)]).iniciarJogo()
    
    def restateJogoBlackjack(self, req: dict):
        idUsuario = req.get("idUsuario")
        nomeUsuario = req.get("nomeUsuario")         
        return Blackjack([JogadorBlackjackModel.newJogadorBlackjack(nome=nomeUsuario, id=idUsuario)]).restateJogo()
