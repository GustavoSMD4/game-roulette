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

        stats = self.__calcularStats(resultados)

        # Formatação bonita da resposta
        resposta = f"""
        🎯 Estatísticas do Jogador: {nomeJogador}

        🎮 Total de Jogos: {stats['totalJogos']}
        🏆 Vitórias: {stats['vitorias']} ({stats['winRate']}%)

        💰 Total Apostado: R$ {stats['totalApostado']:.2f}
        📈 Lucro Total: {'+' if stats['lucroTotal'] >= 0 else '-'}R$ {abs(stats['lucroTotal']):.2f}

        🔴 Apostas em Red: {stats['apostasRed']}
        ⚫ Apostas em Black: {stats['apostasBlack']}
        🔢 Apostas em Números: {stats['apostasNumero']}
        ⭐ Aposta Preferida: {stats['apostaPreferida']}
        """.strip()

        return resposta

    def statsJogadorDict(self, req: dict):
        """Mesmas estatísticas de statsJogador, porém estruturadas para consumo do front."""
        idJogador = req.get("idUsuario")

        if idJogador is None:
            raise Exception("idUsuario vazio")

        usuario = self.__usuarioRepository.consultaPorId(idJogador)
        nomeJogador = req.get("nomeUsuario") or (usuario.getUsuario() if usuario else None)

        if nomeJogador is None:
            raise Exception("nomeUsuario vazio")

        resultados = self.__resultadoRoletaRepo.consultarPorIdJogador(idJogador)

        if not resultados or len(resultados) == 0:
            return {"nomeJogador": nomeJogador, "possuiJogos": False}

        stats = self.__calcularStats(resultados)
        stats["nomeJogador"] = nomeJogador
        stats["possuiJogos"] = True

        return stats

    def statsGeraisDict(self):
        """Mesmas estatísticas de stats(), porém estruturadas para consumo do front."""
        resultados = self.__resultadoRoletaRepo.consultarTodos()

        if not resultados or len(resultados) == 0:
            return {"possuiJogos": False}

        stats = self.__calcularStats(resultados)
        stats["possuiJogos"] = True

        return stats

    def stats(self):
        resultados = self.__resultadoRoletaRepo.consultarTodos()

        if not resultados or len(resultados) == 0:
            return "🎰 Nenhum jogo registrado ainda."

        stats = self.__calcularStats(resultados)

        resposta = f"""
        📊 Estatísticas Gerais da Roleta

        🎮 Total de Jogos: {stats['totalJogos']}
        🏆 Vitórias: {stats['vitorias']} ({stats['winRate']}%)

        💰 Total Apostado: R$ {stats['totalApostado']:.2f}
        📈 Lucro Total: {'+' if stats['lucroTotal'] >= 0 else '-'}R$ {abs(stats['lucroTotal']):.2f}

        🔴 Apostas em Red: {stats['apostasRed']}
        ⚫ Apostas em Black: {stats['apostasBlack']}
        🔢 Apostas em Números: {stats['apostasNumero']}
        ⭐ Aposta Mais Popular: {stats['apostaPreferida']}
        """.strip()

        return resposta

    def __calcularStats(self, resultados: list):
        """Consolida os números das estatísticas usados pelo jogador, pelos gerais e pelo front."""
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

        # Contagem dos tipos de aposta
        vezesApostouRed = sum(1 for r in resultados if str(r.getApostaJogador()).lower() == "red")
        vezesApostouBlack = sum(1 for r in resultados if str(r.getApostaJogador()).lower() == "black")
        vezesApostouNumero = sum(
            1 for r in resultados
            if str(r.getApostaJogador()).lower() not in ["red", "black"]
        )

        tiposAposta = {
            "🔴 Red": vezesApostouRed,
            "⚫ Black": vezesApostouBlack,
            "🔢 Números": vezesApostouNumero
        }

        return {
            "totalJogos": totalJogos,
            "vitorias": vitorias,
            "derrotas": totalJogos - vitorias,
            "winRate": winRate,
            "totalApostado": round(dinheiroTotalApostado, 2),
            "lucroTotal": round(retornoTotalDinheiro, 2),
            "apostasRed": vezesApostouRed,
            "apostasBlack": vezesApostouBlack,
            "apostasNumero": vezesApostouNumero,
            "apostaPreferida": max(tiposAposta, key=tiposAposta.get)
        }
    
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
    
    def jogarDict(self, req: dict):
        """Mesma jogada de play(), porém devolvendo o resultado estruturado para o front."""
        idUsuario = req.get("idUsuario")

        if idUsuario is None:
            raise Exception("idUsuario vazio")

        apostaJogador, tipo = self.__interpretarAposta(req.get("bet"))
        valorAposta = self.__validarValorAposta(req.get("bet_amount"))
        usuario = self.__usuarioRepository.consultaPorId(idUsuario)

        if usuario is None:
            raise Exception("Usuário não encontrado")

        if usuario.getSaldo() < valorAposta:
            raise Exception("Usuário não tem saldo suficiente para realizar essa aposta!")

        return self.__executarJogada(tipo, usuario, apostaJogador, valorAposta)

    def jogar(self, type: str, idUsuario: str, apostaJogador: str, valorAposta: float):
        """Realiza a jogada, altera o Saldo do jogador, registra o resultado da jogada no histórico do servidor e retorna str do resultado"""
        usuario = self.__usuarioRepository.consultaPorId(idUsuario)
        return self.__executarJogada(type, usuario, apostaJogador, valorAposta)["mensagem"]

    def __interpretarAposta(self, aposta):
        # Regra de aposta da roleta fica na classe Roulette, para o modo solo e a mesa usarem a mesma
        return Roulette.newRoulette().interpretarAposta(aposta)

    def __validarValorAposta(self, valorAposta):
        try:
            valor = float(valorAposta)
        except (TypeError, ValueError):
            raise Exception("Valor da aposta precisa ser um número")

        if valor < 1:
            raise Exception("Aposta mínima é 1")

        return valor

    def __separarResultado(self, texto: str):
        partes = str(texto or "").split()

        if len(partes) != 2:
            return None, None

        return partes[0], int(partes[1])

    def __executarJogada(self, tipo: str, usuario, apostaJogador, valorAposta: float):
        novoSaldo = usuario.getSaldo() - valorAposta
        resultado = None

        if tipo == "number":
            resultado = Roulette.newRoulette().playNumber(apostaJogador, valorAposta)

        if tipo == "color":
            resultado = Roulette.newRoulette().playColor(apostaJogador, valorAposta)

        venceu = resultado.get("message") == "You won"
        ganhou = 1 if venceu else 0

        if venceu:
            novoSaldo += resultado.get("amount")

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

        cor, numero = self.__separarResultado(resultado.get("result"))
        valorRecebido = round(float(resultado['amount']), 2) if venceu else 0.0

        return {
            "tipo": tipo,
            "aposta": str(apostaJogador),
            "valorAposta": float(valorAposta),
            "cor": cor,
            "numero": numero,
            "ganhou": venceu,
            "valorRecebido": valorRecebido,
            "lucro": round(valorRecebido - valorAposta, 2),
            "saldo": usuario.getSaldo(),
            "mensagem": mensagem
        }
    
        
        
        
        
