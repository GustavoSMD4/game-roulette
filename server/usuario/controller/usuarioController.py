from flask import Flask, jsonify, request

from server.usuario.repository.usuarioRepo import UsuarioRepo
from server.usuario.model.usuario import Usuario

class UsuarioController:
    def __init__(self, app: Flask):
        self.app = app
        self.__repository = UsuarioRepo.usuarioRepo()
        
    def routes(self):
        @self.app.route("/usuario")
        def usuarioConsulta():
            try:
                dados = self.__repository.consultarTodos()
                return jsonify({"usuarios": dados}), 200
            
            except Exception as e:
                return jsonify({"error": str(e)}), 400
            
        @self.app.route("/usuario/create", methods=["POST"])
        def createUsuario():
            try:
                req: dict = request.json
                usuarioCreate = Usuario.usuario()
                usuarioCreate.setUsuario(req.get("usuario"))
                usuarioCreate.setSenha(req.get("senha"))
                usuarioCreate.setSaldo(req.get("saldo"))
                
                usuarios = self.__repository.create(usuarioCreate)
                return jsonify({"usuarios": usuarios}), 200
            
            except Exception as e:
                return jsonify({"error": str(e)}), 400
            
        @self.app.route("/usuario/update", methods=["POST"])
        def updateUsuario():
            try:
                req: dict = request.json
                
                if req.get("id") is None or req.get("id") == "":
                    return jsonify({"error": "Id vazio!", "code": 400}), 400
                
                usuarioUpdate = Usuario.usuario()
                usuarioUpdate.setId(req.get("id"))
                usuarioUpdate.setUsuario(req.get("usuario"))
                usuarioUpdate.setSenha(req.get("senha"))
                usuarioUpdate.setSaldo(req.get("saldo"))
                
                usuarios = self.__repository.update(usuarioUpdate)
                return jsonify({"usuarios": usuarios}), 200
            
            except Exception as e:
                return jsonify({"error": str(e)}), 500
            