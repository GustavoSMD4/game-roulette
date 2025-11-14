from collections import defaultdict
from datetime import datetime
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
        retornoTotalDinheiro = sum(
            (
                (r.getValorResultado() - r.getValorAposta())  # lucro líquido
                if r.getGanhou() == 1
                else -(r.getValorAposta() or 0)               # perda total
            )
            for r in resultados
        )
        
        lucroTotal = round(retornoTotalDinheiro, 2)

        # Contagem dos tipos de aposta
        vezesApostouRed = sum(1 for r in resultados if str(r.getApostaJogador()).lower() == "red")
        vezesApostouBlack = sum(1 for r in resultados if str(r.getApostaJogador()).lower() == "black")
        vezesApostouNumero = sum(
            1 for r in resultados
            if str(r.getApostaJogador()).lower() not in ["red", "black"]
        )

        # Define aposta preferida
        tiposAposta = {
            "🔴 Red": vezesApostouRed,
            "⚫ Black": vezesApostouBlack,
            "🔢 Números": vezesApostouNumero
        }
        apostaPreferida = max(tiposAposta, key=tiposAposta.get)

        # Formatação bonita da resposta
        stats = f"""
        🎯 Estatísticas do Jogador: {nomeJogador}

        🎮 Total de Jogos: {totalJogos}
        🏆 Vitórias: {vitorias} ({winRate}%)

        💰 Total Apostado: R$ {dinheiroTotalApostado:.2f}
        📈 Lucro Total: {'+' if lucroTotal >= 0 else '-'}R$ {abs(lucroTotal):.2f}

        🔴 Apostas em Red: {vezesApostouRed}
        ⚫ Apostas em Black: {vezesApostouBlack}
        🔢 Apostas em Números: {vezesApostouNumero}
        ⭐ Aposta Preferida: {apostaPreferida}
        """.strip()

        return stats

    def stats(self):
        resultados = self.__resultadoRoletaRepo.consultarTodos()

        if not resultados or len(resultados) == 0:
            return "🎰 Nenhum jogo registrado ainda."

        totalJogos = len(resultados)
        vitorias = sum(1 for r in resultados if r.getGanhou() == 1)
        winRate = round((vitorias / totalJogos) * 100, 2)

        dinheiroTotalApostado = sum(r.getValorAposta() or 0 for r in resultados)

        # Lucro líquido total
        retornoTotalDinheiro = sum(
            (
                (r.getValorResultado() - r.getValorAposta())  # lucro líquido
                if r.getGanhou() == 1
                else -(r.getValorAposta() or 0)               # perda total
            )
            for r in resultados
        )
        lucroTotal = round(retornoTotalDinheiro, 2)

        # Contagem de tipos de aposta
        vezesApostouRed = sum(1 for r in resultados if str(r.getApostaJogador()).lower() == "red")
        vezesApostouBlack = sum(1 for r in resultados if str(r.getApostaJogador()).lower() == "black")
        vezesApostouNumero = sum(
            1 for r in resultados
            if str(r.getApostaJogador()).lower() not in ["red", "black"]
        )

        # Aposta mais popular
        tiposAposta = {
            "🔴 Red": vezesApostouRed,
            "⚫ Black": vezesApostouBlack,
            "🔢 Números": vezesApostouNumero
        }
        apostaMaisPopular = max(tiposAposta, key=tiposAposta.get)

        stats = f"""
        📊 Estatísticas Gerais da Roleta

        🎮 Total de Jogos: {totalJogos}
        🏆 Vitórias: {vitorias} ({winRate}%)

        💰 Total Apostado: R$ {dinheiroTotalApostado:.2f}
        📈 Lucro Total: {'+' if lucroTotal >= 0 else '-'}R$ {abs(lucroTotal):.2f}

        🔴 Apostas em Red: {vezesApostouRed}
        ⚫ Apostas em Black: {vezesApostouBlack}
        🔢 Apostas em Números: {vezesApostouNumero}
        ⭐ Aposta Mais Popular: {apostaMaisPopular}
        """.strip()

        return stats 
    
    def statsPorDia(self):
        resultados = self.__resultadoRoletaRepo.consultarTodos()

        if not resultados or len(resultados) == 0:
            return "🎰 Nenhum jogo registrado ainda."

        statsDiarios = defaultdict(lambda: {
            "totalJogos": 0,
            "vitorias": 0,
            "dinheiroApostado": 0.0,
            "lucro": 0.0,
            "red": 0,
            "black": 0,
            "numero": 0
        })

        for r in resultados:
            data = r.getDataHora()
            if isinstance(data, str):
                data = datetime.fromisoformat(data)
            dia = data.date()

            statsDiarios[dia]["totalJogos"] += 1
            if r.getGanhou() == 1:
                statsDiarios[dia]["vitorias"] += 1
                statsDiarios[dia]["lucro"] += (r.getValorResultado() - r.getValorAposta())
            else:
                statsDiarios[dia]["lucro"] -= r.getValorAposta() or 0

            statsDiarios[dia]["dinheiroApostado"] += r.getValorAposta() or 0

            aposta = str(r.getApostaJogador()).lower()
            if aposta == "red":
                statsDiarios[dia]["red"] += 1
            elif aposta == "black":
                statsDiarios[dia]["black"] += 1
            else:
                statsDiarios[dia]["numero"] += 1

        resposta = "📅 Estatísticas Diárias da Roleta\n"
        for dia, stats in sorted(statsDiarios.items()):
            winRate = round((stats["vitorias"] / stats["totalJogos"]) * 100, 2)
            apostaMaisPopular = max(
                {"🔴 Red": stats["red"], "⚫ Black": stats["black"], "🔢 Números": stats["numero"]},
                key=lambda k: {"🔴 Red": stats["red"], "⚫ Black": stats["black"], "🔢 Números": stats["numero"]}[k]
            )

            resposta += f"""
            📆 {dia}
            🎮 Total de Jogos: {stats['totalJogos']}
            🏆 Vitórias: {stats['vitorias']} ({winRate}%)
            💰 Total Apostado: R$ {stats['dinheiroApostado']:.2f}
            📈 Lucro Total: {'+' if stats['lucro'] >= 0 else '-'}R$ {abs(stats['lucro']):.2f}
            🔴 Red: {stats['red']}, ⚫ Black: {stats['black']}, 🔢 Números: {stats['numero']}
            ⭐ Aposta Mais Popular: {apostaMaisPopular}
            """
            
        return resposta.strip()
    
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

        textMensagemResultado = self.jogar(type, idUsuario, str(bet), betAmount)
        return textMensagemResultado
    
    def jogar(self, type: str, idUsuario: str, apostaJogador: str, valorAposta: float):
        """Realiza a jogada, altera o Saldo do jogador, registra o resultado da jogada no histórico do servidor e retorna str do resultado"""
        usuario = self.__usuarioRepository.consultaPorId(idUsuario)
        novoSaldo = usuario.getSaldo() - valorAposta
        ganhou = 0
        resultado = None
        
        if type == "number":
            resultado = Roulette.newRoulette().playNumber(apostaJogador, valorAposta)
        
        if type == "color":
            resultado = Roulette.newRoulette().playColor(apostaJogador, valorAposta)
        
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
    
        
        
        
        
