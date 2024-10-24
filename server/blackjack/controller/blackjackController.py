from flask import Flask, jsonify

from server.blackjack.repository.blackjackRepo import BlackjackRepo


class BlackjackController:
    def __init__(self, app: Flask, repository: BlackjackRepo):
        self.__app = app
        self.__repository = repository
        
    @classmethod
    def blackjackController(cls, app):
        controller = cls(app, BlackjackRepo.newBlackjackRepo())
        return controller.routes()
    
    def routes(self):
        @self.__app.route("/blackjack", methods=["POST"])
        def blackjack():
            try:
                dados = self.__repository.consultarJogo()
                
                return jsonify({"body": {"jogo": dados}})
            except Exception as e:
                return jsonify({"error": str(e)}), 400