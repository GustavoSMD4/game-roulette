from flask import jsonify
from server.games.roulette import Roulette
from server.roulette.models.resultadoRoletaModel import ResultadoRoleta
from server.roulette.repository.resultadoRoletaRepo import ResultadoRoletaRepo
from server.usuario.repository.usuarioRepo import UsuarioRepo
from server.usuario.service.usuarioService import UsuarioService


class RouletteService:
    def __init__(self, resultadoRoletaRepo: ResultadoRoletaRepo):
        self.__usuarioRepository = UsuarioRepo.newRepo()
        self.__resultadoRoletaRepo = resultadoRoletaRepo
        
    @classmethod
    def newService(cls):
        return cls(ResultadoRoletaRepo.newRepo())
    
    def statsJogador(self, req: dict):
        idJogador = req.get("idUsuario")
        nomeJogador = req.get("nomeUsuario")
        
        if idJogador is None:
            raise Exception("idUsuario vazio")
        
        if nomeJogador is None:
            raise Exception("nomeUsuario vazio")
        
        resultados = self.__resultadoRoletaRepo.consultarPorIdJogador(idJogador)

        if not resultados or len(resultados) == 0:
            return f"🎰 Jogador {nomeJogador} ainda não possui jogos registrados."

        totalJogos = len(resultados)
        vitorias = sum(1 for r in resultados if r.getGanhou() == 1)
        winRate = round((vitorias / totalJogos) * 100, 2)

        dinheiroTotalApostado = sum(r.getValorAposta() or 0 for r in resultados)

        # Retorno total considerando ganhos e perdas
        retornoTotalDinheiro = sum((r.getValorResultado() if r.getGanhou() == 1 else -(r.getValorResultado() or 0)) for r in resultados)
        
        lucroTotal = round(retornoTotalDinheiro, 2)

        vezesApostouRed = sum(1 for r in resultados if str(r.getApostaJogador()).lower() == "red")
        vezesApostouBlack = sum(1 for r in resultados if str(r.getApostaJogador()).lower() == "black")

        if vezesApostouRed > vezesApostouBlack:
            apostaPreferida = "🔴 Red"
        elif vezesApostouBlack > vezesApostouRed:
            apostaPreferida = "⚫ Black"
        else:
            apostaPreferida = "⚪ Empate (Red/Black)"

        # Formatação bonita da resposta
        stats = f"""
        🎯 Estatísticas do Jogador: {nomeJogador}

        🎮 Total de Jogos: {totalJogos}
        🏆 Vitórias: {vitorias} ({winRate}%)

        💰 Total Apostado: R$ {dinheiroTotalApostado:.2f}
        📈 Lucro Total: {'+' if lucroTotal >= 0 else '-'}R$ {abs(lucroTotal):.2f}

        🔴 Apostas em Red: {vezesApostouRed}
        ⚫ Apostas em Black: {vezesApostouBlack}
        ⭐ Aposta Preferida: {apostaPreferida}
        """.strip()

        return stats
    
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
            textMensagemResultado = self.__resultadoJogada(Roulette.newRoulette().playNumber(bet, betAmount), idUsuario, str(bet), betAmount)
            return jsonify({"mensagem": textMensagemResultado}), 200

        if type == "color":
            textMensagemResultado = self.__resultadoJogada(Roulette.newRoulette().playColor(bet, betAmount), idUsuario, bet, betAmount)
            return jsonify({"mensagem": textMensagemResultado}), 200
    
    def __resultadoJogada(self, resultado: dict, idUsuario: str, apostaJogador: str, valorAposta: float):
        """Altera o Saldo, registra o resultado da jogada no histórico do servidor e retorna str do resultado"""
        usuario = self.__usuarioRepository.consultaPorId(idUsuario)
        novoSaldo = usuario.getSaldo() - valorAposta
        ganhou = 0
        
        if resultado.get("message") == "You won":
            novoSaldo += resultado.get("amount")
            ganhou = 1
            
        usuario.setSaldo(novoSaldo)
        self.__usuarioRepository.update(usuario)
        valorResultado = resultado['amount'] if resultado['amount'] > 0 else str(resultado['amount'])
        
        mensagem = (
            f"🎰 **Resultado da Roleta**\n"
            f"• Aposta: **{apostaJogador}**\n"
            f"• Valor apostado: **R$ {valorAposta}**\n"
            f"• Resultado: **{resultado['result']}**\n"
            f"• Status: **{resultado['message']}**\n"
            f"• Valor resultado: **R$ {valorResultado}**\n"
            f"• Usuário: **{usuario.getUsuario()}**\n"
            f"• Saldo atualizado: **R$ {usuario.getSaldo()}**"
        )
        
        resultadoModel = ResultadoRoleta.newModel()
        resultadoModel.setIdJogador(usuario.getId())
        resultadoModel.setApostaJogador(apostaJogador)
        resultadoModel.setValorAposta(valorAposta)
        resultadoModel.setResultado(resultado['result'])
        resultadoModel.setValorResultado(valorResultado)
        resultadoModel.setGanhou(ganhou)
        self.__resultadoRoletaRepo.create(resultadoModel)
        
        return mensagem
    
        
        
        
        
