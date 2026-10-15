import logging
from flask import Flask, jsonify, request
from flask_limiter import Limiter
from server.roulette.service.rouletteService import RouletteService

class RouletteController:
    def __init__(self, app: Flask, limiter: Limiter = None, logger: logging = None):
        self.app = app
        self.limiter = limiter
        self.logger = logger
        
    @classmethod
    def newController(cls, app, limiter = None, logger = None):
        return cls(app, limiter, logger).routes()

    def __service(self):
        # Um service por requisição: conexões/cursors do sqlite não são compartilháveis entre threads
        return RouletteService.newService()
    
    def routes(self):
        @self.app.route("/roulette/play", methods=["POST"])
        @self.limiter.limit("20 per minute")
        def playRoulette():
            try:
                textMensagemResultado = self.__service().play(request.json)
                return jsonify({"mensagem": textMensagemResultado}), 200
                
            except Exception as e:
                return jsonify({"error": str(e)}), 400
            
        @self.app.route("/roulette/stats", methods=["POST"])
        @self.limiter.limit("10 per minute")
        def rouletteStats():
            try:
                stats = self.__service().statsJogador(request.json)
                return jsonify({"body": {"stats": stats}})
                
            except Exception as e:
                return jsonify({"error": str(e)}), 400
            
        @self.app.route("/roulette/stats/gerais")
        @self.limiter.limit("10 per minute")
        def rouletteStatsGerais():
            try:
                stats = self.__service().stats()
                return jsonify({"body": {"stats": stats}})
                
            except Exception as e:
                return jsonify({"error": str(e)}), 400
            
        @self.app.route("/roulette/stats/dia")
        @self.limiter.limit("10 per minute")
        def rouletteStatsDia():
            try:
                stats = self.__service().statsPorDia()
                return jsonify({"body": {"stats": stats}})
                
            except Exception as e:
                return jsonify({"error": str(e)}), 400