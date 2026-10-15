from flask import Flask, jsonify, request
from flask_limiter import Limiter

from server.usuario.repository.usuarioRepo import UsuarioRepo
from server.usuario.model.usuario import Usuario
from server.usuario.service.usuarioService import UsuarioService

class UsuarioController:
    def __init__(self, app, limiter: Limiter = None, logger = None):
        self.app = app
        self.limiter = limiter
        self.__logger = logger

    @classmethod
    def newController(cls, app: Flask, limiter: Limiter = None, logger = None):
        return cls(app, limiter, logger).routes()

    def __repository(self):
        # Um repositório por requisição: conexões/cursors do sqlite não são compartilháveis entre threads
        return UsuarioRepo.newRepo()

    def __service(self):
        return UsuarioService.newService()
        
    def routes(self):
        @self.app.route("/usuario")
        def usuarioConsulta():
            try:
                dados = self.__repository().consultarTodos()
                return jsonify({"usuarios": dados}), 200
            
            except Exception as e:
                return jsonify({"error": str(e)}), 400
            
        @self.app.route("/login", methods=["POST"])
        def login():
            try:
                usuario = self.__service().verificarUsuario(request.json)
                return jsonify({"usuario": usuario.getDictUsuario()}), 200
            
            except Exception as e:
                return jsonify({"error": str(e)}), 400
            
        @self.app.route("/usuario/depositar", methods=["POST"])
        @self.limiter.limit("10 per minute")
        def depositar():
            try:
                usuario = self.__service().depositar(request.json)
                return jsonify({"usuario": usuario.getDictUsuario()}), 200
            
            except Exception as e:
                return jsonify({"error": str(e)}), 400
                
            
        # @self.app.route("/usuario/create", methods=["POST"])
        # def createUsuario():
        #     try:
        #         req: dict = request.json
        #         usuarioCreate = Usuario.usuario()
        #         usuarioCreate.setUsuario(req.get("usuario"))
        #         usuarioCreate.setSenha(req.get("senha"))
        #         usuarioCreate.setSaldo(req.get("saldo"))
                
        #         usuarios = self.__repository().create(usuarioCreate)
        #         return jsonify({"usuarios": usuarios}), 200
            
        #     except Exception as e:
        #         return jsonify({"error": str(e)}), 400
            
        # @self.app.route("/usuario/update", methods=["POST"])
        # def updateUsuario():
        #     try:
        #         req: dict = request.json
        #         usuarioUpdate = Usuario.usuario()
        #         usuarioUpdate.setUsuario(req.get("usuario"))
        #         usuarioUpdate.setSenha(req.get("senha"))
        #         usuarioUpdate.setSaldo(req.get("saldo"))
                
        #         usuarios = self.__repository().update(usuarioUpdate)
        #         return jsonify({"usuarios": usuarios}), 200
            
        #     except Exception as e:
        #         return jsonify({"error": str(e)}), 500
            