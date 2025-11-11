from flask import Flask, jsonify, request

from server.blackjack.repository.blackjackRepo import BlackjackRepo
from server.blackjack.service.blackjackService import BlackjackService


class BlackjackController:
    def __init__(self, app: Flask, repository: BlackjackRepo, service: BlackjackService):
        self.__app = app
        self.__service = service
        self.__repository = repository
        
    @classmethod
    def blackjackController(cls, app):
        controller = cls(app, BlackjackRepo.newBlackjackRepo(), BlackjackService.blackjackService())
        return controller.routes()
    
    def routes(self):
        @self.__app.route("/blackjack", methods=["POST"])
        def blackjack():
            try:
                dados = self.__repository.consultarJogo(request.json.get("idJogo"))
                
                return jsonify({"body": {"jogo": dados}})
            except Exception as e:
                return jsonify({"error": str(e)}), 400
            
        @self.__app.route("/blackjack/create", methods=["POST"])
        def createJogo():
            try:
                idJogoCriado = self.__service.createNovoJogoBlackjack(request.json)
                jogoCriado = self.__repository.consultarJogo(idJogoCriado)
                
                return jsonify({"body": {"jogo": jogoCriado}})
            except Exception as e:
                return jsonify({"error": str(e)}), 400