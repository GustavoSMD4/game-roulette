from classes.blackjack import Blackjack
from server.blackjack.repository.blackjackRepo import BlackjackRepo
from server.blackjack.service.blackjackService import BlackjackService
from server.roulette.service.rouletteService import RouletteService
from server.usuario.model.usuario import Usuario
from server.usuario.repository.usuarioRepo import UsuarioRepo
from server.usuario.service.usuarioService import UsuarioService


class FrontService:
    def __init__(self, usuarioRepo: UsuarioRepo, usuarioService: UsuarioService, blackjackRepo: BlackjackRepo,
                 rouletteService: RouletteService, blackjackService: BlackjackService):
        self.__usuarioRepo = usuarioRepo
        self.__usuarioService = usuarioService
        self.__blackjackRepo = blackjackRepo
        self.__rouletteService = rouletteService
        self.__blackjackService = blackjackService

    @classmethod
    def newService(cls):
        return cls(UsuarioRepo.newRepo(), UsuarioService.newService(), BlackjackRepo.newBlackjackRepo(),
                   RouletteService.newService(), BlackjackService.blackjackService())

    def login(self, req: dict):
        usuario = req.get("usuario")
        senha = req.get("senha")

        if not usuario or not senha:
            raise Exception("Informe usuário e senha")

        dados = self.__usuarioRepo.login(usuario, senha)

        if not dados:
            raise Exception("Usuário ou senha inválidos")

        return Usuario.newUsuario(dados[0])

    def criarConta(self, req: dict):
        usuario = req.get("usuario")
        senha = req.get("senha")

        if not usuario or not senha:
            raise Exception("Informe usuário e senha")

        if any(u.getUsuario() == usuario for u in self.__usuarioRepo.consultarTodos()):
            raise Exception("Usuário já existe")

        novoUsuario = Usuario.newUsuario()
        novoUsuario.setUsuario(usuario)
        novoUsuario.setSenha(senha)
        novoUsuario.setSaldo(0)

        self.__usuarioRepo.create(novoUsuario)

        return self.__usuarioRepo.consultarPorUsuario(usuario)

    def consultarConta(self, idUsuario):
        usuario = self.__usuarioRepo.consultaPorId(self.__converterId(idUsuario))

        if usuario is None:
            raise Exception("Usuário não encontrado")

        return usuario

    def depositar(self, req: dict):
        try:
            valor = float(req.get("valor"))
        except (TypeError, ValueError):
            raise Exception("Valor para depositar inválido")

        usuario = self.consultarConta(req.get("idUsuario"))

        return self.__usuarioService.depositar({
            "idUsuario": usuario.getId(),
            "nomeUsuario": usuario.getUsuario(),
            "saldo": valor
        })

    @staticmethod
    def __converterId(idUsuario):
        try:
            return int(idUsuario)
        except (TypeError, ValueError):
            raise Exception("Usuário inválido")

    def iniciarBlackjack(self, req: dict):
        return Blackjack.iniciarJogoDict(self.__converterId(req.get("idUsuario")), req.get("valorAposta"))

    def consultarBlackjack(self, req: dict):
        idUsuario = self.__converterId(req.get("idUsuario"))

        if self.__blackjackRepo.consultarJogoIdJogador(idUsuario) is None:
            return {
                "ativo": False,
                "finalizado": True,
                "idJogo": None,
                "jogadorHost": None,
                "dealer": None,
                "jogadores": [],
                "acoes": [],
                "mensagem": None,
                "resultado": None
            }

        return Blackjack.restateJogoDict(idUsuario)

    def jogarBlackjack(self, req: dict):
        jogada = req.get("jogada")

        if jogada is None:
            raise Exception("Informe a jogada")

        return Blackjack.jogadaJogadorDict(self.__converterId(req.get("idUsuario")), int(jogada))

    def estatisticasJogador(self, req: dict):
        return self.__rouletteService.statsJogadorDict({"idUsuario": self.__converterId(req.get("idUsuario"))})

    def estatisticasGerais(self):
        return self.__rouletteService.statsGeraisDict()

    def estatisticasBlackjack(self, req: dict):
        return self.__blackjackService.estatisticasJogador({"idUsuario": self.__converterId(req.get("idUsuario"))})

    def estatisticasBlackjackGerais(self):
        return self.__blackjackService.estatisticasGerais()

    def replayBlackjack(self, req: dict):
        return self.__blackjackService.replayMao({
            "idJogo": req.get("idJogo"),
            "indiceMao": req.get("indiceMao")
        })

    def listarJogadores(self):
        jogadores = []

        for usuario in self.__usuarioRepo.consultarTodos():
            if usuario.getUsuario() == "dealer":
                continue

            roleta = self.__rouletteService.statsJogadorDict({"idUsuario": usuario.getId()})
            blackjackCompleto = self.__blackjackService.estatisticasJogador({"idUsuario": usuario.getId()})
            blackjack = blackjackCompleto.get("stats", {})

            jogadores.append({
                "id": str(usuario.getId()),
                "usuario": usuario.getUsuario(),
                "saldo": usuario.getSaldo(),
                "geral": self.__combinarStats(roleta, blackjack),
                "roleta": {
                    "jogos": roleta.get("totalJogos", 0),
                    "lucro": roleta.get("lucroTotal", 0.0)
                },
                "blackjack": {
                    "maos": blackjack.get("totalJogos", 0),
                    "lucro": blackjack.get("lucroTotal", 0.0)
                }
            })

        jogadores.sort(key=lambda jogador: jogador["usuario"].lower())

        return {"jogadores": jogadores, "geral": self.estatisticasGeralServidor()}

    def estatisticasGeralServidor(self):
        """Resumo do servidor juntando roleta e blackjack de todos os jogadores."""
        roleta = self.__rouletteService.statsGeraisDict()
        blackjack = self.__blackjackService.estatisticasGerais().get("stats", {})

        return {
            "possuiJogos": roleta.get("possuiJogos") or blackjack.get("possuiJogos"),
            "geral": self.__combinarStats(roleta, blackjack),
            "roleta": roleta,
            "blackjack": blackjack
        }

    @staticmethod
    def __combinarStats(roleta: dict, blackjack: dict):
        jogos = int(roleta.get("totalJogos") or 0) + int(blackjack.get("totalJogos") or 0)
        vitorias = int(roleta.get("vitorias") or 0) + int(blackjack.get("vitorias") or 0)
        derrotas = int(roleta.get("derrotas") or 0) + int(blackjack.get("derrotas") or 0)
        empates = int(blackjack.get("empates") or 0)
        totalApostado = round(float(roleta.get("totalApostado") or 0) + float(blackjack.get("totalApostado") or 0), 2)
        lucroTotal = round(float(roleta.get("lucroTotal") or 0) + float(blackjack.get("lucroTotal") or 0), 2)

        return {
            "possuiJogos": jogos > 0,
            "jogos": jogos,
            "vitorias": vitorias,
            "derrotas": derrotas,
            "empates": empates,
            "taxaVitoria": round((vitorias / jogos) * 100, 2) if jogos else 0,
            "totalApostado": totalApostado,
            "lucroTotal": lucroTotal,
            "apostaMedia": round(totalApostado / jogos, 2) if jogos else 0
        }

    def estatisticasDeJogador(self, req: dict):
        idUsuario = self.__converterId(req.get("idUsuario"))
        usuario = self.consultarConta(idUsuario)
        roleta = self.__rouletteService.statsJogadorDict({"idUsuario": idUsuario, "nomeUsuario": usuario.getUsuario()})
        blackjack = self.__blackjackService.estatisticasJogador({"idUsuario": idUsuario})

        return {
            "jogador": {
                "id": str(usuario.getId()),
                "usuario": usuario.getUsuario(),
                "saldo": usuario.getSaldo()
            },
            "geral": self.__combinarStats(roleta, blackjack.get("stats", {})),
            "roleta": roleta,
            "blackjack": blackjack
        }

    def jogarRoleta(self, req: dict):
        return self.__rouletteService.jogarDict({
            "idUsuario": self.__converterId(req.get("idUsuario")),
            "bet": req.get("bet"),
            "bet_amount": req.get("bet_amount")
        })
