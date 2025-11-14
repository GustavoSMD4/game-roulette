from classes.blackjack import Blackjack
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
        return Blackjack.iniciarJogo(idUsuario, nomeUsuario)
    
    def restateJogoBlackjack(self, req: dict):
        idUsuario = req.get("idUsuario")
        nomeUsuario = req.get("nomeUsuario")         
        return Blackjack.restateJogo(idUsuario, nomeUsuario)

    def jogar(self, req: dict):
        idUsuario = req.get("idUsuario")
        nomeUsuario = req.get("nomeUsuario")
        jogada = req.get("jogada")
        return Blackjack.jogadaJogador(idUsuario, nomeUsuario, jogada)