from classes.blackjack import Blackjack
from server.blackjack.models.acaoBlackjackModel import AcaoBlackjack
from server.blackjack.models.resultadoBlackjackModel import ResultadoBlackjack
from server.blackjack.repository.acaoBlackjackRepo import AcaoBlackjackRepo
from server.blackjack.repository.blackjackRepo import BlackjackRepo
from server.blackjack.repository.resultadoBlackjackRepo import ResultadoBlackjackRepo


class BlackjackService:
    def __init__(self, repository: BlackjackRepo, resultadoRepo: ResultadoBlackjackRepo, acaoRepo: AcaoBlackjackRepo):
        self.__repository = repository
        self.__resultadoRepo = resultadoRepo
        self.__acaoRepo = acaoRepo
        
    @classmethod
    def blackjackService(cls):
        return cls(BlackjackRepo.newBlackjackRepo(), ResultadoBlackjackRepo.newRepo(), AcaoBlackjackRepo.newRepo())
    
    def createNovoJogoBlackjack(self, req: dict):
        idUsuario = req.get("idUsuario")
        return Blackjack.iniciarJogo(idUsuario)
    
    def restateJogoBlackjack(self, req: dict):
        idUsuario = req.get("idUsuario")
        return Blackjack.restateJogo(idUsuario)

    def jogar(self, req: dict):
        idUsuario = req.get("idUsuario")
        jogada = req.get("jogada")
        return Blackjack.jogadaJogador(idUsuario, jogada=jogada)

    def estatisticasJogador(self, req: dict):
        """Estatísticas e histórico de mãos do jogador."""
        idUsuario = req.get("idUsuario")

        if idUsuario is None:
            raise Exception("idUsuario vazio")

        resultados = self.__resultadoRepo.consultarPorIdJogador(idUsuario)

        return {
            "possuiJogos": len(resultados) > 0,
            "stats": self.__calcularStats(resultados),
            "historico": [self.__maoDict(r) for r in self.__resultadoRepo.consultarUltimosPorJogador(idUsuario, 20)]
        }

    def estatisticasGerais(self):
        """Estatísticas gerais do blackjack (todos os jogadores)."""
        resultados = self.__resultadoRepo.consultarTodos()

        return {
            "possuiJogos": len(resultados) > 0,
            "stats": self.__calcularStats(resultados)
        }

    def __calcularStats(self, resultados: list):
        totalJogos = len(resultados)

        if totalJogos == 0:
            return {
                "possuiJogos": False,
                "totalJogos": 0, "vitorias": 0, "derrotas": 0, "empates": 0, "winRate": 0,
                "totalApostado": 0, "lucroTotal": 0, "apostaMedia": 0, "maiorGanho": 0, "maiorPerda": 0
            }

        vitorias = sum(1 for r in resultados if (r.getLucro() or 0) > 0)
        derrotas = sum(1 for r in resultados if (r.getLucro() or 0) < 0)
        lucros = [r.getLucro() or 0 for r in resultados]
        totalApostado = sum(r.getValorAposta() or 0 for r in resultados)

        return {
            "possuiJogos": True,
            "totalJogos": totalJogos,
            "vitorias": vitorias,
            "derrotas": derrotas,
            "empates": totalJogos - vitorias - derrotas,
            "winRate": round((vitorias / totalJogos) * 100, 2),
            "totalApostado": round(totalApostado, 2),
            "lucroTotal": round(sum(lucros), 2),
            "apostaMedia": round(totalApostado / totalJogos, 2),
            "maiorGanho": round(max(max(lucros), 0), 2),
            "maiorPerda": round(min(min(lucros), 0), 2)
        }

    def replayMao(self, req: dict):
        """Passo a passo de uma mão (cartas iniciais, ações do jogador e cartas do dealer)."""
        idJogo = req.get("idJogo")

        if not idJogo:
            raise Exception("idJogo vazio")

        indiceMao = int(req.get("indiceMao") or 0)
        resultado = self.__resultadoRepo.consultarPorJogo(idJogo, indiceMao)

        if resultado is None:
            raise Exception("Mão não encontrada")

        return {
            "idJogo": idJogo,
            "indiceMao": indiceMao,
            "resultado": self.__maoDict(resultado),
            "acoes": [self.__acaoDict(acao) for acao in self.__acaoRepo.consultarPorJogo(idJogo, indiceMao)]
        }

    def __acaoDict(self, acao: AcaoBlackjack):
        return {
            "acao": acao.getAcao(),
            "dono": acao.getDono(),
            "indiceMao": acao.getIndiceMao(),
            "carta": acao.getCarta(),
            "valorJogador": acao.getValorJogador(),
            "valorDealer": acao.getValorDealer(),
            "dataHora": acao.getDataHora()
        }

    def __maoDict(self, resultado: ResultadoBlackjack):
        resumo = Blackjack.RESUMOS_RESULTADO.get(resultado.getResultado(), {})

        return {
            "id": resultado.getId(),
            "idJogo": resultado.getIdJogo(),
            "indiceMao": resultado.getIndiceMao(),
            "resultado": resultado.getResultado(),
            "situacao": resumo.get("situacao"),
            "titulo": resumo.get("titulo"),
            "descricao": resumo.get("descricao"),
            "valorAposta": resultado.getValorAposta(),
            "valorJogador": resultado.getValorJogador(),
            "valorDealer": resultado.getValorDealer(),
            "valorRecebido": resultado.getValorRecebido(),
            "lucro": resultado.getLucro(),
            "dataHora": resultado.getDataHora()
        }