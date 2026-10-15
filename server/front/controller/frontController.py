import logging
import os

from flask import Flask, jsonify, request, send_from_directory
from flask_limiter import Limiter

from server.front.service.frontService import FrontService

FRONT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEMPLATES_DIR = os.path.join(FRONT_DIR, "templates")
STATIC_DIR = os.path.join(FRONT_DIR, "static")
ASSETS_DIR = os.path.join(os.path.dirname(FRONT_DIR), "..", "assets")


class FrontController:
    def __init__(self, app: Flask, limiter: Limiter = None, logger: logging = None):
        self.__app = app
        self.__limiter = limiter
        self.__logger = logger

    @classmethod
    def newController(cls, app: Flask, limiter: Limiter = None, logger: logging = None):
        return cls(app, limiter, logger).routes()

    def __service(self) -> FrontService:
        # Um service por requisição: as conexões/cursors do sqlite não podem ser compartilhados entre threads
        return FrontService.newService()

    def __limite(self, regra: str):
        if self.__limiter is None:
            return lambda func: func

        return self.__limiter.limit(regra)

    @staticmethod
    def __dictUsuario(usuario):
        # O ID é enviado como texto porque os IDs do banco excedem o limite seguro de número do JavaScript
        return {
            "id": str(usuario.getId()),
            "usuario": usuario.getUsuario(),
            "saldo": usuario.getSaldo()
        }

    def routes(self):
        @self.__app.route("/")
        def frontRaiz():
            return send_from_directory(TEMPLATES_DIR, "login.html")

        @self.__app.route("/front/login")
        def frontLogin():
            return send_from_directory(TEMPLATES_DIR, "login.html")

        @self.__app.route("/front/criar-conta")
        def frontCriarConta():
            return send_from_directory(TEMPLATES_DIR, "criarConta.html")

        @self.__app.route("/front/conta")
        def frontConta():
            return send_from_directory(TEMPLATES_DIR, "conta.html")

        @self.__app.route("/front/roleta")
        def frontRoleta():
            return send_from_directory(TEMPLATES_DIR, "roleta.html")

        @self.__app.route("/front/blackjack")
        def frontBlackjack():
            return send_from_directory(TEMPLATES_DIR, "blackjack.html")

        @self.__app.route("/front/estatisticas")
        def frontEstatisticas():
            return send_from_directory(TEMPLATES_DIR, "estatisticas.html")

        @self.__app.route("/front/static/<path:filename>")
        def frontStatic(filename):
            return send_from_directory(STATIC_DIR, filename)

        @self.__app.route("/assets/<path:filename>")
        def frontAssets(filename):
            return send_from_directory(ASSETS_DIR, filename)

        @self.__app.route("/front/api/login", methods=["POST"])
        @self.__limite("60 per minute")
        def frontApiLogin():
            try:
                usuario = self.__service().login(request.json or {})
                return jsonify({"usuario": self.__dictUsuario(usuario)}), 200

            except Exception as e:
                return jsonify({"error": str(e)}), 400

        @self.__app.route("/front/api/criar-conta", methods=["POST"])
        @self.__limite("60 per minute")
        def frontApiCriarConta():
            try:
                usuario = self.__service().criarConta(request.json or {})
                return jsonify({"usuario": self.__dictUsuario(usuario)}), 201

            except Exception as e:
                return jsonify({"error": str(e)}), 400

        @self.__app.route("/front/api/conta")
        def frontApiConta():
            try:
                usuario = self.__service().consultarConta(request.args.get("idUsuario"))
                return jsonify({"usuario": self.__dictUsuario(usuario)}), 200

            except Exception as e:
                return jsonify({"error": str(e)}), 400

        @self.__app.route("/front/api/depositar", methods=["POST"])
        @self.__limite("10000 per minute")
        def frontApiDepositar():
            try:
                usuario = self.__service().depositar(request.json or {})
                return jsonify({"usuario": self.__dictUsuario(usuario)}), 200

            except Exception as e:
                return jsonify({"error": str(e)}), 400

        @self.__app.route("/front/api/blackjack/iniciar", methods=["POST"])
        @self.__limite("60 per minute")
        def frontApiBlackjackIniciar():
            try:
                estado = self.__service().iniciarBlackjack(request.json or {})
                return jsonify(estado), 200

            except Exception as e:
                return jsonify({"error": str(e)}), 400

        @self.__app.route("/front/api/blackjack/estado", methods=["POST"])
        @self.__limite("120 per minute")
        def frontApiBlackjackEstado():
            try:
                estado = self.__service().consultarBlackjack(request.json or {})
                return jsonify(estado), 200

            except Exception as e:
                return jsonify({"error": str(e)}), 400

        @self.__app.route("/front/api/blackjack/jogar", methods=["POST"])
        @self.__limite("120 per minute")
        def frontApiBlackjackJogar():
            try:
                estado = self.__service().jogarBlackjack(request.json or {})
                return jsonify(estado), 200

            except Exception as e:
                return jsonify({"error": str(e)}), 400

        @self.__app.route("/front/api/estatisticas", methods=["POST"])
        @self.__limite("60 per minute")
        def frontApiEstatisticas():
            try:
                stats = self.__service().estatisticasJogador(request.json or {})
                return jsonify({"stats": stats}), 200

            except Exception as e:
                return jsonify({"error": str(e)}), 400

        @self.__app.route("/front/api/estatisticas/gerais")
        @self.__limite("60 per minute")
        def frontApiEstatisticasGerais():
            try:
                stats = self.__service().estatisticasGerais()
                return jsonify({"stats": stats}), 200

            except Exception as e:
                return jsonify({"error": str(e)}), 400

        @self.__app.route("/front/api/blackjack/estatisticas", methods=["POST"])
        @self.__limite("60 per minute")
        def frontApiBlackjackEstatisticas():
            try:
                return jsonify(self.__service().estatisticasBlackjack(request.json or {})), 200

            except Exception as e:
                return jsonify({"error": str(e)}), 400

        @self.__app.route("/front/api/blackjack/estatisticas/gerais")
        @self.__limite("60 per minute")
        def frontApiBlackjackEstatisticasGerais():
            try:
                return jsonify(self.__service().estatisticasBlackjackGerais()), 200

            except Exception as e:
                return jsonify({"error": str(e)}), 400

        @self.__app.route("/front/api/jogadores")
        @self.__limite("60 per minute")
        def frontApiJogadores():
            try:
                return jsonify(self.__service().listarJogadores()), 200

            except Exception as e:
                return jsonify({"error": str(e)}), 400

        @self.__app.route("/front/api/jogadores/estatisticas", methods=["POST"])
        @self.__limite("60 per minute")
        def frontApiJogadorEstatisticas():
            try:
                return jsonify(self.__service().estatisticasDeJogador(request.json or {})), 200

            except Exception as e:
                return jsonify({"error": str(e)}), 400

        @self.__app.route("/front/api/roulette/jogar", methods=["POST"])
        @self.__limite("60 per minute")
        def frontApiRouletteJogar():
            try:
                return jsonify(self.__service().jogarRoleta(request.json or {})), 200

            except Exception as e:
                return jsonify({"error": str(e)}), 400

        @self.__app.route("/front/api/blackjack/replay", methods=["POST"])
        @self.__limite("120 per minute")
        def frontApiBlackjackReplay():
            try:
                return jsonify(self.__service().replayBlackjack(request.json or {})), 200

            except Exception as e:
                return jsonify({"error": str(e)}), 400
