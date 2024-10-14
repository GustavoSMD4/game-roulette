from flask import Response, jsonify
from server.games.roulette import Roulette
from server.usuario.repository.usuarioRepo import UsuarioRepo


class PlayService:
    def __init__(self):
        self.__usuarioRepository = UsuarioRepo.usuarioRepo()
        
    @classmethod
    def playService(cls):
        return cls()
    
    def play(self, usuario, bet, betAmount, type):
        
        usuarioConsultado = self.__usuarioRepository.consultarPorUsuario(usuario)
        
        if usuarioConsultado.getSaldo() < betAmount:
            return jsonify({"error": "Usuário não tem saldo suficiente para realizar essa aposta!"}), 400
        
        if type not in ["number", "color"]:
            raise Exception("Types only color or number")

        if type == "number":
            return jsonify(Roulette.newRoulette().playNumber(bet, betAmount)), 200

        if type == "color":
            return jsonify(Roulette.newRoulette().playColor(bet, betAmount)), 200

        
        
        
        
        
        