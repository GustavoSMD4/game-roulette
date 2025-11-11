from flask import jsonify
from server.games.roulette import Roulette
from server.usuario.repository.usuarioRepo import UsuarioRepo
from server.usuario.service.usuarioService import UsuarioService


class RouletteService:
    def __init__(self):
        self.__usuarioRepository = UsuarioRepo.newRepo()
        
    @classmethod
    def newService(cls):
        return cls()
    
    def play(self, req: dict):
        idUsuario = req.get("idUsuario")
        nomeUsuario = req.get("usuario")
        bet = req.get("bet")
        betAmount = req.get("bet_amount")
        type = "color"
        
        try:
            type = int(bet)
            type = "number"
        except:
            type = "color"
            
        usuario = UsuarioService.newService().verificarUsuario(req)
        
        if betAmount < 1:
            return jsonify({"error": "Aposta mínima é 1"}), 400
        
        if not isinstance(betAmount, int):
            return jsonify({"error": "Valor da aposta só pode ser números inteiros!"}), 400
                
        if usuario.getSaldo() < betAmount:
            raise Exception("Usuário não tem saldo suficiente para realizar essa aposta!")
        
        if type not in ["number", "color"]:
            raise Exception("Types only color or number")

        if type == "number":
            resultado, usuarioAtualizado = self.__alterarSaldoJogadorAposJogada(Roulette.newRoulette().playNumber(bet, betAmount), idUsuario, betAmount)
            r = resultado
            u = usuarioAtualizado.getDictUsuario()
            valorResultado = r['amount'] if r['amount'] > 0 else str(r['amount'])

            mensagem = (
                f"🎰 **Resultado da Roleta**\n"
                f"• Aposta: **{bet}**\n"
                f"• Valor apostado: **R$ {betAmount}**\n"
                f"• Resultado: **{r['result']}**\n"
                f"• Status: **{r['message']}**\n"
                f"• Valor resultado: **R$ {valorResultado}**\n"
                f"• Usuário: **{u['usuario']}**\n"
                f"• Saldo atualizado: **R$ {u['saldo']}**"
            )

            return jsonify({"mensagem": mensagem}), 200

        if type == "color":
            resultado, usuarioAtualizado = self.__alterarSaldoJogadorAposJogada(Roulette.newRoulette().playColor(bet, betAmount), idUsuario, betAmount)
            r = resultado
            u = usuarioAtualizado.getDictUsuario()
            valorResultado = r['amount'] if r['amount'] > 0 else str(r['amount'])

            mensagem = (
                f"🎰 **Resultado da Roleta**\n"
                f"• Aposta: **{bet}**\n"
                f"• Valor apostado: **R$ {betAmount}**\n"
                f"• Resultado: **{r['result']}**\n"
                f"• Status: **{r['message']}**\n"
                f"• Valor resultado: **R$ {valorResultado}**\n"
                f"• Usuário: **{u['usuario']}**\n"
                f"• Saldo atualizado: **R$ {u['saldo']}**"
            )

            return jsonify({"mensagem": mensagem}), 200

        
    def __alterarSaldoJogadorAposJogada(self, resultado: dict, idUsuario: str, valorAposta: float):
        usuario = self.__usuarioRepository.consultaPorId(idUsuario)
        
        novoSaldo = usuario.getSaldo() - valorAposta
        
        if resultado.get("message") == "You won":
            novoSaldo += resultado.get("amount")
            
        usuario.setSaldo(novoSaldo)
        self.__usuarioRepository.update(usuario)
        
        return resultado, usuario
    
        
        
        
        
