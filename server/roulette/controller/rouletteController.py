import logging
from flask import Flask, jsonify, request
from flask_limiter import Limiter
from server.roulette.service.rouletteService import RouletteService

class RouletteController:
    def __init__(self, app: Flask, service: RouletteService, limiter: Limiter, logger: logging):
        self.app = app
        self.__service = service
        self.limiter = limiter
        self.logger = logger
        
    @classmethod
    def newController(cls, app, limiter = None, logger = None):
        return cls(app, RouletteService.newService(), limiter, logger).routes()
    
    def routes(self):
        @self.app.route("/roulette/play", methods=["POST"])
        @self.limiter.limit("10 per minute")
        def playRoulette():
            try:
                return self.__service.play(request.json)
                
            except Exception as e:
                return jsonify({"error": str(e)}), 400