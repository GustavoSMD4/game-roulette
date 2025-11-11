from flask import Flask, jsonify, request

from server.usuario.repository.usuarioRepo import UsuarioRepo
from server.usuario.model.usuario import Usuario
from server.usuario.service.usuarioService import UsuarioService

class UsuarioController:
    def __init__(self, app, repository: UsuarioRepo, usuarioService: UsuarioService):
        self.app = app
        self.__repository = repository
        self.__service = usuarioService
        
    @classmethod
    def newController(cls, app: Flask):
        return cls(app, UsuarioRepo.newRepo(), UsuarioService.newService()).routes()
        
    def routes(self):
        @self.app.route("/usuario")
        def usuarioConsulta():
            try:
                dados = self.__repository.consultarTodos()
                return jsonify({"usuarios": dados}), 200
            
            except Exception as e:
                return jsonify({"error": str(e)}), 400
            
        @self.app.route("/login", methods=["POST"])
        def login():
            try:
                usuario = self.__service.verificarUsuario(request.json)
                return jsonify({"usuario": usuario.getDictUsuario()}), 200
            
            except Exception as e:
                return jsonify({"error": str(e)}), 400
            
        @self.app.route("/usuario/depositar", methods=["POST"])
        def depositar():
            try:
                usuario = self.__service.depositar(request.json)
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
                
        #         usuarios = self.__repository.create(usuarioCreate)
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
                
        #         usuarios = self.__repository.update(usuarioUpdate)
        #         return jsonify({"usuarios": usuarios}), 200
            
        #     except Exception as e:
        #         return jsonify({"error": str(e)}), 500
            