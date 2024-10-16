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
        
        if betAmount < 1:
            return jsonify({"error": "Aposta mínima é 1"}), 400
        
        if not isinstance(betAmount, int):
            return jsonify({"error": "Valor da aposta só pode ser números inteiros!"}), 400
        
        usuarioConsultado = self.__usuarioRepository.consultarPorUsuario(usuario)
        
        if usuarioConsultado.getSaldo() < betAmount:
            return jsonify({"error": "Usuário não tem saldo suficiente para realizar essa aposta!"}), 400
        
        if type not in ["number", "color"]:
            raise Exception("Types only color or number")

        if type == "number":
            resultado, usuarioAtualizado = self.__alterarSaldoJogadorAposJogada(Roulette.newRoulette().playNumber(bet, betAmount), usuario, betAmount)
            return jsonify({"resultado": resultado, "usuario": usuarioAtualizado}), 200

        if type == "color":
            resultado, usuarioAtualizado = self.__alterarSaldoJogadorAposJogada(Roulette.newRoulette().playColor(bet, betAmount), usuario, betAmount)
            return jsonify({"resultado": resultado, "usuario": usuarioAtualizado.getDictUsuario()}), 200

        
    def __alterarSaldoJogadorAposJogada(self, resultado: dict, nomeUsuario: str, valorAposta: float):
        usuario = self.__usuarioRepository.consultarPorUsuario(nomeUsuario)
        
        novoSaldo = usuario.getSaldo() - valorAposta
        
        if resultado.get("message") == "You won":
            novoSaldo += resultado.get("amount")
            
        usuario.setSaldo(novoSaldo)
        self.__usuarioRepository.update(usuario)
        
        return resultado, usuario
    
        
        
        
        