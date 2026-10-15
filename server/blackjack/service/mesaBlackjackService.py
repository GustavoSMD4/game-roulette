import threading
import uuid
from datetime import timedelta

from classes.baralhoFromDb import BaralhoDb
from classes.blackjack import Blackjack
from classes.carta import Carta
from classes.jogador import Jogador
from server.blackjack.models.acaoBlackjackModel import AcaoBlackjack
from server.blackjack.models.blackjackModel import BlackjackModel
from server.blackjack.models.resultadoBlackjackModel import ResultadoBlackjack
from server.blackjack.repository.acaoBlackjackRepo import AcaoBlackjackRepo
from server.blackjack.repository.blackjackRepo import BlackjackRepo
from server.blackjack.repository.resultadoBlackjackRepo import ResultadoBlackjackRepo
from server.blackjack.repository.rodadaBlackjackRepo import RodadaBlackjackRepo
from server.blackjack.repository.salaBlackjackRepo import SalaBlackjackRepo
from server.roulette.service import chatSessao, presencaMesa
from server.usuario.repository.usuarioRepo import UsuarioRepo
from utils import agoraBrasilia, agoraBrasiliaData

# Mesa ao vivo: 10 segundos de apostas, 15 segundos por decisao, depois dealer e resultado geral
DURACAO_APOSTA = 10
DURACAO_DECISAO = 15
DURACAO_DEALER = 4
DURACAO_RESULTADO = 6

DURACAO_SALA_MINUTOS = 60
GRACA_EXPIRACAO_MINUTOS = 10
LIMITE_HISTORICO = 12
LIMITE_JOGADORES = 6
QTDE_BARALHOS = 4
MAXIMO_MAOS = 4
APOSTA_MINIMA = 1.0
APOSTA_MAXIMA = Blackjack.APOSTA_MAXIMA

COMANDOS = {"comprar": "comprar", "parar": "parar", "dobrar": "dobrar", "dividir": "dividir"}

# O Flask atende em varias threads e o SQLite tem um escritor por vez: serializa o avanco da mesa
CADEADO_MESA = threading.Lock()


class MesaBlackjackService:
    """Mesa de blackjack ao vivo: apostas com tempo, turnos, dealer unico e resultado geral.

    O relogio anda o jogo (sem timers de fundo): cada requisicao verifica se a janela de apostas
    fechou, se o tempo de decisao venceu e se o dealer ja pode jogar. O estado completo da mesa
    fica em JSON na rodada, entao todos veem exatamente a mesma mesa e recarregar nao muda nada.
    """

    def __init__(self, salaRepo: SalaBlackjackRepo, rodadaRepo: RodadaBlackjackRepo,
                 resultadoRepo: ResultadoBlackjackRepo, usuarioRepo: UsuarioRepo,
                 acaoRepo: AcaoBlackjackRepo = None, blackjackRepo: BlackjackRepo = None):
        self.__salaRepo = salaRepo
        self.__rodadaRepo = rodadaRepo
        self.__resultadoRepo = resultadoRepo
        self.__usuarioRepo = usuarioRepo
        self.__acaoRepo = acaoRepo or AcaoBlackjackRepo.newRepo()
        self.__blackjackRepo = blackjackRepo or BlackjackRepo.newBlackjackRepo()

    @classmethod
    def newService(cls):
        return cls(SalaBlackjackRepo.newRepo(), RodadaBlackjackRepo.newRepo(),
                   ResultadoBlackjackRepo.newRepo(), UsuarioRepo.newRepo(),
                   AcaoBlackjackRepo.newRepo(), BlackjackRepo.newBlackjackRepo())

    # ------------------------------------------------------------- sala

    def criarSala(self, req: dict):
        idUsuario = self.__converterId(req.get("idUsuario"))
        usuario = self.__usuarioRepo.consultaPorId(idUsuario) if idUsuario is not None else None

        if usuario is None:
            raise Exception("Usuário não encontrado")

        agora = agoraBrasiliaData()
        nome = str(req.get("nome") or "").strip() or f"Mesa de {usuario.getUsuario()}"

        with CADEADO_MESA:
            self.__limparSalasExpiradas(agora)
            sala = self.__salaRepo.criar(nome[:60], usuario.getId(), agora, agora + timedelta(minutes=DURACAO_SALA_MINUTOS))
            self.__rodadaRepo.criar(sala.getId(), "apostando", agora, agora + timedelta(seconds=DURACAO_APOSTA),
                                    self.__novoEstado(self.__novaSemente()))

        return {
            "sala": self.__dictSala(sala),
            "mensagem": f"Sala criada! O link vale por {DURACAO_SALA_MINUTOS} minutos."
        }

    def enviarMensagem(self, req: dict):
        idUsuario = self.__converterId(req.get("idUsuario"))
        usuario = self.__usuarioRepo.consultaPorId(idUsuario) if idUsuario is not None else None

        if usuario is None:
            raise Exception("Usuário não encontrado")

        with CADEADO_MESA:
            sala = self.__sala(req.get("codigo"))

            if sala.isExpirada(agoraBrasiliaData()):
                raise Exception("Esta sala já expirou")

        return {"mensagem": chatSessao.enviar(sala.getCodigo(), usuario.getId(), usuario.getUsuario(), req.get("texto"))}

    # ------------------------------------------------------------- apostas

    def apostar(self, req: dict):
        idUsuario = self.__converterId(req.get("idUsuario"))

        if idUsuario is None:
            raise Exception("Usuário inválido")

        valor = self.__validarValor(req.get("valor"))

        with CADEADO_MESA:
            sala = self.__sala(req.get("codigo"))
            agora = agoraBrasiliaData()

            if sala.isExpirada(agora):
                raise Exception("Esta sala já expirou. Crie uma nova para jogar com os amigos.")

            rodada = self.__avancar(self.__rodadaAtual(sala), agora)

            if rodada.getFase() != "apostando":
                raise Exception("As apostas desta rodada já fecharam. Espere a próxima.")

            usuario = self.__usuarioRepo.consultaPorId(idUsuario)

            if usuario is None:
                raise Exception("Usuário não encontrado")

            if usuario.getSaldo() < valor:
                raise Exception("Saldo insuficiente para essa aposta. Deposite mais para continuar jogando.")

            estado = rodada.getEstado()
            chave = str(usuario.getId())

            if chave not in estado["jogadores"] and len(estado["ordem"]) >= LIMITE_JOGADORES:
                raise Exception(f"A mesa está cheia ({LIMITE_JOGADORES} jogadores)")

            jogador = estado["jogadores"].setdefault(chave, self.__novoJogador(usuario))
            jogador["aposta"] = round(jogador["aposta"] + valor, 2)

            if chave not in estado["ordem"]:
                estado["ordem"].append(chave)

            self.__debitar(usuario, valor)
            estado["mensagem"] = f"{usuario.getUsuario()} apostou {self.__formatar(valor)}."
            rodada = self.__salvar(rodada.getId(), "apostando", rodada.getDataHoraFimFase(), estado)

        return self.__montarEstado(sala, rodada, idUsuario, req.get("desdeChat", 0))

    # ------------------------------------------------------------- jogadas

    def jogar(self, req: dict):
        idUsuario = self.__converterId(req.get("idUsuario"))
        comando = str(req.get("comando") or "").strip().lower()

        if idUsuario is None:
            raise Exception("Usuário inválido")

        if comando not in COMANDOS:
            raise Exception("Jogada inválida")

        with CADEADO_MESA:
            sala = self.__sala(req.get("codigo"))
            agora = agoraBrasiliaData()

            if sala.isExpirada(agora):
                raise Exception("Esta sala já expirou. Crie uma nova para jogar com os amigos.")

            rodada = self.__avancar(self.__rodadaAtual(sala), agora)

            if rodada.getFase() != "jogando":
                raise Exception("Não há mão em andamento nesta rodada")

            estado = rodada.getEstado()
            jogador = estado["jogadores"].get(str(idUsuario))

            if jogador is None:
                raise Exception("Você não apostou nesta rodada")

            daVez = self.__jogadorDaVez(estado)

            if daVez is None or daVez["idJogador"] != str(idUsuario):
                nome = daVez["nome"] if daVez else "outro jogador"
                raise Exception(f"Não é a sua vez. Agora é a vez de {nome}.")

            usuario = self.__usuarioRepo.consultaPorId(idUsuario)
            mao = self.__maoAtual(jogador)

            if mao is None:
                raise Exception("Você não tem mão em andamento")

            self.__aplicarJogada(comando, jogador, mao, estado, usuario)
            estado["mensagem"] = f"{jogador['nome']} {self.__descricaoComando(comando)}."

            rodada = self.__salvar(rodada.getId(), "jogando", agora + timedelta(seconds=DURACAO_DECISAO), estado)
            rodada = self.__andarTurno(rodada, agora)

        return self.__montarEstado(sala, rodada, idUsuario, req.get("desdeChat", 0))

    def __aplicarJogada(self, comando, jogador, mao, estado, usuario):
        if comando == "comprar":
            carta = self.__darCarta(estado)
            mao["cartas"].append(carta)
            self.__registrarPasso(estado, jogador, mao["indice"], "comprar", "jogador", carta,
                                  self.__valorMao(mao["cartas"]))
            return

        if comando == "parar":
            mao["encerrada"] = True
            self.__registrarPasso(estado, jogador, mao["indice"], "parar", "jogador", None,
                                  self.__valorMao(mao["cartas"]))
            return

        if comando == "dobrar":
            if len(mao["cartas"]) != 2:
                raise Exception("Só é possível dobrar nas duas primeiras cartas")

            if usuario is None or usuario.getSaldo() < mao["aposta"]:
                raise Exception("Saldo insuficiente para dobrar a aposta")

            self.__debitar(usuario, mao["aposta"])
            mao["aposta"] = round(mao["aposta"] * 2, 2)
            carta = self.__darCarta(estado)
            mao["cartas"].append(carta)
            mao["encerrada"] = True
            self.__registrarPasso(estado, jogador, mao["indice"], "dobrar", "jogador", carta,
                                  self.__valorMao(mao["cartas"]))
            return

        cartas = mao["cartas"]

        if len(cartas) != 2 or cartas[0]["valor"] != cartas[1]["valor"]:
            raise Exception("Só é possível dividir com duas cartas de mesmo valor")

        if len(jogador["maos"]) >= MAXIMO_MAOS:
            raise Exception(f"Limite de {MAXIMO_MAOS} mãos por jogador")

        if usuario is None or usuario.getSaldo() < mao["aposta"]:
            raise Exception("Saldo insuficiente para dividir a mão")

        self.__debitar(usuario, mao["aposta"])

        separada = cartas.pop(1)
        cartaAtual = self.__darCarta(estado)
        mao["cartas"].append(cartaAtual)

        nova = self.__novaMao(len(jogador["maos"]), mao["aposta"], [separada, self.__darCarta(estado)])
        jogador["maos"].insert(jogador["indiceMaoAtual"] + 1, nova)
        self.__renumerarMaos(jogador)

        # o replay e gravado depois de renumerar: o indice da mao nova so existe a partir dai
        self.__registrarPasso(estado, jogador, mao["indice"], "dividir", "jogador", None,
                              self.__valorMao(mao["cartas"]))
        self.__registrarPasso(estado, jogador, mao["indice"], "inicio", "jogador", cartaAtual,
                              self.__valorMao(mao["cartas"]))
        self.__registrarInicioDaMao(estado, jogador, nova)

    # ------------------------------------------------------------- estado

    def estado(self, req: dict = None):
        req = req or {}
        idUsuario = self.__converterId(req.get("idUsuario"))

        with CADEADO_MESA:
            sala = self.__sala(req.get("codigo"))
            agora = agoraBrasiliaData()

            if sala.isExpirada(agora):
                return self.__estadoExpirado(sala, idUsuario)

            self.__limparSalasExpiradas(agora)
            rodada = self.__avancar(self.__rodadaAtual(sala), agora)

        return self.__montarEstado(sala, rodada, idUsuario, req.get("desdeChat", 0))

    # ------------------------------------------------------------- relogio da mesa

    def __rodadaAtual(self, sala):
        rodada = self.__rodadaRepo.consultarAtual(sala.getId())

        if rodada is None:
            agora = agoraBrasiliaData()
            rodada = self.__rodadaRepo.criar(sala.getId(), "apostando", agora,
                                             agora + timedelta(seconds=DURACAO_APOSTA),
                                             self.__novoEstado(self.__novaSemente()))

        return rodada

    def __avancar(self, rodada, agora):
        if rodada.getFase() == "apostando":
            if agora < rodada.getDataHoraFimFase():
                return rodada

            if not rodada.getEstado().get("ordem"):
                return self.__salvar(rodada.getId(), "apostando", agora + timedelta(seconds=DURACAO_APOSTA),
                                     rodada.getEstado(), "Ninguém apostou ainda. As apostas seguem abertas.")

            return self.__iniciarMao(rodada, agora)

        if rodada.getFase() == "jogando":
            return self.__andarTurno(rodada, agora)

        if rodada.getFase() == "dealer":
            if agora >= rodada.getDataHoraFimFase():
                return self.__liquidar(rodada, agora)

            return rodada

        if agora >= rodada.getDataHoraFimFase():
            return self.__novaRodada(rodada, agora)

        return rodada

    def __iniciarMao(self, rodada, agora):
        estado = rodada.getEstado()

        for idJogador in estado["ordem"]:
            jogador = estado["jogadores"][idJogador]
            jogador["maos"] = [self.__novaMao(0, jogador["aposta"], self.__darCartas(estado, 2))]
            jogador["indiceMaoAtual"] = 0
            jogador["finalizado"] = False
            jogador["lucro"] = None
            jogador["resultados"] = []
            self.__abrirJogoDaMesa(rodada, jogador)
            self.__registrarInicioDaMao(estado, jogador, jogador["maos"][0])

        estado["dealer"] = self.__darCartas(estado, 2)

        for carta in estado["dealer"]:
            self.__registrarCartaDealer(estado, carta, "inicio")
        estado["participantes"] = None
        estado["turno"] = 0
        estado["mensagem"] = "Cartas dadas! Cada um joga na sua vez."
        self.__normalizarMaos(estado)
        self.__posicionarPrimeiroTurno(estado)

        return self.__salvar(rodada.getId(), "jogando", agora + timedelta(seconds=DURACAO_DECISAO), estado)

    def __andarTurno(self, rodada, agora):
        estado = rodada.getEstado()
        fim = rodada.getDataHoraFimFase()
        mudouTurno = False
        mensagem = estado.get("mensagem")

        for _ in range(64):
            if self.__todosFinalizados(estado):
                return self.__faseDealer(rodada, agora, estado)

            jogador = self.__jogadorDaVez(estado)

            if jogador is None:
                self.__proximoJogador(estado)
                mudouTurno = True
                continue

            mao = self.__maoAtual(jogador)

            # mão estourada ou com 21: acabou, passa para a próxima
            if mao is not None and (mao["encerrada"] or self.__valorMao(mao["cartas"]) >= 21):
                self.__encerrarMao(jogador, mao, estado)
                mudouTurno = self.__proximaMaoOuJogador(jogador, estado) or mudouTurno
                continue

            # tempo de decisão vencido: a mão para sozinha
            if agora >= fim:
                if mao is not None:
                    mao["encerrada"] = True
                mensagem = f"Tempo de decisão esgotado - a mão de {jogador['nome']} parou automaticamente."
                mudouTurno = self.__proximaMaoOuJogador(jogador, estado) or mudouTurno
                continue

            if mao is None:
                mudouTurno = self.__proximaMaoOuJogador(jogador, estado) or mudouTurno
                continue

            # alguém precisa decidir: para aqui
            if mudouTurno:
                fim = agora + timedelta(seconds=DURACAO_DECISAO)

            return self.__salvar(rodada.getId(), "jogando", fim, estado, mensagem)

        return self.__salvar(rodada.getId(), "jogando", fim, estado, mensagem)

    def __faseDealer(self, rodada, agora, estado):
        self.__jogarDealer(estado)
        estado["mensagem"] = "Vez do dealer."
        return self.__salvar(rodada.getId(), "dealer", agora + timedelta(seconds=DURACAO_DEALER), estado)

    def __liquidar(self, rodada, agora):
        estado = rodada.getEstado()
        valorDealer = self.__valorMao(estado["dealer"])
        cartasDealer = len(estado["dealer"])
        totalApostado = 0.0
        totalPago = 0.0
        ganharam = 0
        perderam = 0
        empataram = 0

        for idJogador in estado["ordem"]:
            jogador = estado["jogadores"][idJogador]
            jogador["resultados"] = []
            recebido = 0.0
            apostado = 0.0

            for mao in jogador["maos"]:
                valorJogador = self.__valorMao(mao["cartas"])
                motivo = Blackjack.motivoDoResultado(valorJogador, valorDealer, len(mao["cartas"]), cartasDealer)
                resumo = Blackjack.resumoDoMotivo(motivo)
                multiplicador = Blackjack.pagamentoDoMotivo(motivo)
                pago = round(mao["aposta"] * multiplicador, 2)
                lucro = round(pago - mao["aposta"], 2)

                mao.update({
                    "motivo": motivo,
                    "valor": valorJogador,
                    "recebido": pago,
                    "lucro": lucro,
                    "titulo": resumo["titulo"],
                    "situacao": resumo["situacao"],
                    "encerrada": True
                })

                apostado = round(apostado + mao["aposta"], 2)
                recebido = round(recebido + pago, 2)
                jogador["resultados"].append(mao)
                totalPago = round(totalPago + pago, 2)
                self.__registrarHistorico(jogador, mao, valorDealer, motivo, pago, lucro)

            jogador["apostaTotal"] = apostado
            jogador["recebido"] = recebido
            jogador["lucro"] = round(recebido - apostado, 2)
            jogador["finalizado"] = True
            totalApostado = round(totalApostado + apostado, 2)

            if jogador.get("idJogo"):
                # o registro do jogo só existia para o replay poder agrupar as mãos dessa rodada
                self.__blackjackRepo.deleteJogo(jogador["idJogo"])
                jogador["idJogo"] = None

            if jogador["lucro"] > 0:
                ganharam += 1
            elif jogador["lucro"] < 0:
                perderam += 1
            else:
                empataram += 1

            if recebido > 0:
                self.__creditar(jogador["idJogador"], recebido, estado)

        estado["resultados"] = {
            "ganharam": ganharam,
            "perderam": perderam,
            "empataram": empataram,
            "totalApostado": totalApostado,
            "totalPago": totalPago,
            "valorDealer": valorDealer,
            "cartasDealer": cartasDealer
        }
        estado["mensagem"] = f"Rodada encerrada - dealer fez {valorDealer}."

        return self.__salvar(rodada.getId(), "resultado", agora + timedelta(seconds=DURACAO_RESULTADO), estado)

    def __novaRodada(self, rodada, agora):
        return self.__rodadaRepo.criar(rodada.getIdSala(), "apostando", agora,
                                       agora + timedelta(seconds=DURACAO_APOSTA),
                                       self.__novoEstado(self.__novaSemente()))

    def __salvar(self, idRodada, fase, fimFase, estado, mensagem=None):
        if mensagem is not None:
            estado["mensagem"] = mensagem

        return self.__rodadaRepo.atualizar(idRodada, fase, fimFase, estado)

    # ------------------------------------------------------------- apoio de mãos

    def __novoEstado(self, semente):
        return {
            "semente": semente,
            "usadas": 0,
            "dealer": [],
            "ordem": [],
            "turno": 0,
            "jogadores": {},
            "resultados": None,
            "mensagem": "Apostas abertas!"
        }

    def __novoJogador(self, usuario):
        return {
            "idJogador": str(usuario.getId()),
            "nome": usuario.getUsuario(),
            "aposta": 0.0,
            "maos": [],
            "indiceMaoAtual": 0,
            "finalizado": False,
            "lucro": None,
            "resultados": []
        }

    def __novaMao(self, indice, aposta, cartas):
        return {
            "indice": int(indice),
            "aposta": round(float(aposta), 2),
            "cartas": list(cartas),
            "encerrada": False,
            "valor": 0,
            "recebido": 0.0,
            "lucro": None,
            "motivo": None,
            "titulo": None,
            "situacao": None
        }

    @staticmethod
    def __renumerarMaos(jogador):
        for indice, mao in enumerate(jogador["maos"]):
            mao["indice"] = indice

    def __normalizarMaos(self, estado):
        """Mãos que já nasceram com 21 (blackjack) não precisam de decisão."""
        for idJogador in estado["ordem"]:
            jogador = estado["jogadores"][idJogador]

            for mao in jogador["maos"]:
                if self.__valorMao(mao["cartas"]) >= 21:
                    mao["encerrada"] = True

    def __posicionarPrimeiroTurno(self, estado):
        estado["turno"] = 0
        self.__pularJogadoresSemMao(estado)

    def __pularJogadoresSemMao(self, estado):
        for _ in range(len(estado["ordem"]) + 1):
            jogador = self.__jogadorDaVez(estado)

            if jogador is None:
                return

            if any(not mao["encerrada"] for mao in jogador["maos"]):
                return

            self.__proximoJogador(estado)

    def __jogadorDaVez(self, estado):
        ordem = estado.get("ordem") or []

        if not ordem:
            return None

        if estado["turno"] >= len(ordem):
            estado["turno"] = 0

        return estado["jogadores"].get(ordem[estado["turno"]])

    def __maoAtual(self, jogador):
        if jogador is None:
            return None

        maos = jogador.get("maos") or []

        if not maos:
            return None

        if jogador["indiceMaoAtual"] >= len(maos):
            jogador["indiceMaoAtual"] = len(maos) - 1

        return maos[jogador["indiceMaoAtual"]]

    def __proximoJogador(self, estado):
        ordem = estado.get("ordem") or []

        if not ordem:
            return

        estado["turno"] = (estado["turno"] + 1) % len(ordem)

    def __proximaMaoOuJogador(self, jogador, estado):
        """Passa para a próxima mão do mesmo jogador ou para o próximo jogador. Diz se mudou de turno."""
        for indice, mao in enumerate(jogador["maos"]):
            if not mao["encerrada"]:
                mudou = jogador["indiceMaoAtual"] != indice
                jogador["indiceMaoAtual"] = indice
                return mudou

        self.__proximoJogador(estado)
        jogador["indiceMaoAtual"] = 0
        return True

    def __todosFinalizados(self, estado):
        for idJogador in estado.get("ordem") or []:
            jogador = estado["jogadores"][idJogador]

            if any(not mao["encerrada"] for mao in jogador["maos"]):
                return False

        return True

    def __encerrarMao(self, jogador, mao, estado):
        if self.__valorMao(mao["cartas"]) >= 21:
            mao["encerrada"] = True

    def __jogarDealer(self, estado):
        while True:
            valor = self.__valorMao(estado["dealer"])

            if valor >= 17:
                return

            carta = self.__darCarta(estado)
            estado["dealer"].append(carta)
            self.__registrarCartaDealer(estado, carta, "dealer")

    # ------------------------------------------------------------- cartas

    @staticmethod
    def __novaSemente():
        return uuid.uuid4().int % 1000000000

    def __darCarta(self, estado):
        return self.__darCartas(estado, 1)[0]

    def __darCartas(self, estado, quantidade):
        """Tira cartas do sapato. O baralho é reproduzido pela semente, então a mão nunca muda."""
        baralho = BaralhoDb.newBaralhoFromDb(QTDE_BARALHOS, estado["semente"]).getCartas()
        cartas = []

        for _ in range(quantidade):
            indice = estado["usadas"] % len(baralho)
            estado["usadas"] += 1
            carta = baralho[indice]
            cartas.append({
                "posicao": indice,
                "id": carta.getId(),
                "suit": carta.getSuit(),
                "rank": carta.getRank(),
                "valor": carta.getValor(),
                "nomeImagem": carta.getNomeImagem()
            })

        return cartas

    @staticmethod
    def __valorMao(cartas):
        jogador = Jogador.newJogador(0, "mao")

        for carta in cartas:
            jogador.addCard(Carta.newCarta(carta))

        return jogador.getValorMao()

    @staticmethod
    def __valoresParciais(cartas):
        jogador = Jogador.newJogador(0, "mao")

        for carta in cartas:
            jogador.addCard(Carta.newCarta(carta))

        return jogador.getValoresParciais()

    # ------------------------------------------------------------- historico e saldo

    def __registrarHistorico(self, jogador, mao, valorDealer, motivo, pago, lucro):
        historico = ResultadoBlackjack.newModel()
        historico.setIdJogo(jogador.get("idJogo"))
        historico.setIdJogador(jogador["idJogador"])
        historico.setIndiceMao(mao.get("indice", 0))
        historico.setValorAposta(mao["aposta"])
        historico.setResultado(motivo)
        historico.setValorJogador(mao["valor"])
        historico.setValorDealer(valorDealer)
        historico.setValorRecebido(pago)
        historico.setLucro(lucro)
        historico.setDataHora(agoraBrasilia())
        self.__resultadoRepo.create(historico)

    # ------------------------------------------------------------- replay da mao

    def __abrirJogoDaMesa(self, rodada, jogador):
        """Cria o jogo que agrupa os passos da mão: é o que o histórico usa para o replay.

        O dono fica marcado como "mesa", então o blackjack solo nunca confunde esse registro
        com um jogo em andamento.
        """
        jogo = self.__blackjackRepo.createNovoJogo(BlackjackModel.newBlackjackModel(dict(
            idJogadorHost=f"mesa:{rodada.getIdSala()}",
            valorAposta=round(float(jogador.get("apostaTotal") or jogador.get("aposta") or 0), 2)
        )))
        jogador["idJogo"] = jogo.getId()

    def __registrarInicioDaMao(self, estado, jogador, mao):
        for posicao, carta in enumerate(mao["cartas"]):
            self.__registrarPasso(estado, jogador, mao["indice"], "inicio", "jogador", carta,
                                  self.__valorMao(mao["cartas"][:posicao + 1]))

    def __registrarCartaDealer(self, estado, carta, acao):
        """As cartas do dealer valem para todas as mãos: no replay ficam com índice -1."""
        for idJogador in estado.get("ordem") or []:
            jogador = estado["jogadores"][idJogador]

            if jogador.get("idJogo"):
                self.__registrarPasso(estado, jogador, -1, acao, "dealer", carta, 0)

    def __registrarPasso(self, estado, jogador, indiceMao, acao, dono, carta=None, valorMao=0):
        if not jogador or not jogador.get("idJogo"):
            return

        registro = AcaoBlackjack.newModel()
        registro.setIdJogo(jogador["idJogo"])
        registro.setIdJogador(jogador["idJogador"])
        registro.setIndiceMao(indiceMao)
        registro.setAcao(acao)
        registro.setDono(dono)
        registro.setCarta(carta.get("nomeImagem") if carta else None)
        registro.setValorJogador(valorMao)
        registro.setValorDealer(self.__valorMao(estado["dealer"]) if estado.get("dealer") else 0)
        registro.setDataHora(agoraBrasilia())
        self.__acaoRepo.create(registro)

    def __debitar(self, usuario, valor):
        usuario.setSaldo(round(usuario.getSaldo() - valor, 2))
        self.__usuarioRepo.update(usuario)

    def __creditar(self, idJogador, valor, estado):
        usuario = self.__usuarioRepo.consultaPorId(int(idJogador))

        if usuario is None:
            return

        usuario.setSaldo(round(usuario.getSaldo() + valor, 2))
        self.__usuarioRepo.update(usuario)

        if estado.get("participantes"):
            estado["participantes"][str(idJogador)] = usuario.getSaldo()

    # ------------------------------------------------------------- resposta

    def __montarEstado(self, sala, rodada, idUsuario, desdeChat=0):
        estado = rodada.getEstado()
        presencaMesa.marcar(sala.getCodigo(), idUsuario, self.__nomeDe(idUsuario))
        presentes = [presente["idJogador"] for presente in presencaMesa.presentes(sala.getCodigo())]
        fase = rodada.getFase()
        daVez = self.__jogadorDaVez(estado) if fase == "jogando" else None
        revelarDealer = fase in ("dealer", "resultado")
        valorDealer = self.__valorMao(estado["dealer"]) if estado["dealer"] else 0

        jogadores = []
        for idJogador in estado.get("ordem") or []:
            jogador = estado["jogadores"][idJogador]
            jogadores.append(self.__dictJogador(jogador, daVez, idUsuario, revelarDealer))

        meu = next((item for item in jogadores if item["idJogador"] == str(idUsuario)), None)
        usuarioAtual = self.__usuarioRepo.consultaPorId(int(idUsuario))

        if meu is not None:
            meu["saldo"] = usuarioAtual.getSaldo() if usuarioAtual else 0

        return {
            "meuSaldo": usuarioAtual.getSaldo() if usuarioAtual else 0,
            "sala": self.__dictSala(sala),
            "fase": fase,
            "segundosRestantes": rodada.segundosRestantes(agoraBrasiliaData()),
            "idRodada": rodada.getId(),
            "numeroRodada": rodada.getNumero(),
            "mensagem": estado.get("mensagem"),
            "mensagemGeral": (estado.get("resultados") or {}).get("totalApostado"),
            "dealer": {
                "cartas": estado["dealer"],
                "valoresParciais": self.__valoresParciais(estado["dealer"]) if estado["dealer"] else [],
                "valor": valorDealer if revelarDealer else self.__valorMao(estado["dealer"][:1]) if estado["dealer"] else 0,
                "valorFinal": valorDealer,
                "revelado": revelarDealer
            },
            "jogadores": jogadores,
            "meu": meu,
            "minhasAcoes": self.__acoes(meu, estado, fase, idUsuario),
            "turno": {
                "idJogador": daVez["idJogador"] if daVez else None,
                "nome": daVez["nome"] if daVez else None
            },
            "resultados": estado.get("resultados"),
            "participantes": presentes,
            "presenca": presencaMesa.presentes(sala.getCodigo()),
            "historico": self.__historico(),
            "chat": chatSessao.novas(sala.getCodigo(), desdeChat),
            "duracao": {
                "aposta": DURACAO_APOSTA,
                "decisao": DURACAO_DECISAO,
                "dealer": DURACAO_DEALER,
                "resultado": DURACAO_RESULTADO
            },
            "apostaMinima": APOSTA_MINIMA,
            "apostaMaxima": APOSTA_MAXIMA,
            "expirada": False
        }

    def __dictJogador(self, jogador, daVez, idUsuario, revelarDealer):
        maos = []

        for mao in jogador["maos"]:
            maos.append({
                "indice": mao["indice"],
                "aposta": mao["aposta"],
                "cartas": mao["cartas"],
                "valoresParciais": self.__valoresParciais(mao["cartas"]),
                "valor": self.__valorMao(mao["cartas"]),
                "encerrada": mao["encerrada"],
                "recebido": mao.get("recebido", 0.0),
                "lucro": mao.get("lucro"),
                "titulo": mao.get("titulo"),
                "situacao": mao.get("situacao")
            })

        return {
            "idJogador": jogador["idJogador"],
            "nome": jogador["nome"],
            "aposta": round(float(jogador.get("aposta") or 0), 2),
            "apostaTotal": round(float(jogador.get("apostaTotal") or jogador.get("aposta") or 0), 2),
            "maos": maos,
            "indiceMaoAtual": jogador.get("indiceMaoAtual", 0),
            "minhaVez": bool(daVez and daVez["idJogador"] == jogador["idJogador"]),
            "eu": jogador["idJogador"] == str(idUsuario),
            "finalizado": bool(jogador.get("finalizado")),
            "lucro": jogador.get("lucro"),
            "recebido": jogador.get("recebido")
        }

    def __acoes(self, meu, estado, fase, idUsuario):
        if fase != "jogando" or meu is None or not meu["minhaVez"]:
            return []

        jogador = estado["jogadores"].get(str(idUsuario))
        mao = self.__maoAtual(jogador) if jogador else None

        if mao is None or mao["encerrada"]:
            return []

        usuario = self.__usuarioRepo.consultaPorId(int(idUsuario))
        saldo = usuario.getSaldo() if usuario else 0
        duasCartas = len(mao["cartas"]) == 2
        podeDividir = duasCartas and mao["cartas"][0]["valor"] == mao["cartas"][1]["valor"] and len(jogador["maos"]) < MAXIMO_MAOS

        return [
            self.__acao("comprar", "Comprar", "Pede mais uma carta", True, ""),
            self.__acao("parar", "Parar", "Fica com a mão atual", True, ""),
            self.__acao("dobrar", "Dobrar", "Dobra a aposta e recebe uma carta",
                        duasCartas and saldo >= mao["aposta"],
                        "Só nas duas primeiras cartas e com saldo para dobrar" if not duasCartas else "Saldo insuficiente para dobrar"),
            self.__acao("dividir", "Dividir", "Separa em duas mãos",
                        podeDividir and saldo >= mao["aposta"],
                        "Precisa de duas cartas de mesmo valor e saldo para dividir")
        ]

    @staticmethod
    def __acao(comando, nome, descricao, habilitada, motivo):
        return {
            "comando": comando,
            "nome": nome,
            "descricao": descricao,
            "habilitada": bool(habilitada),
            "motivoIndisponivel": "" if habilitada else motivo
        }

    def __historico(self):
        resultados = list(reversed(self.__resultadoRepo.consultarUltimos(LIMITE_HISTORICO)))
        nomes = {str(usuario.getId()): usuario.getUsuario() for usuario in self.__usuarioRepo.consultarTodos()}

        return [
            {
                "idJogador": str(resultado.getIdJogador()),
                "nome": nomes.get(str(resultado.getIdJogador()), "Jogador"),
                "valorAposta": resultado.getValorAposta(),
                "valorJogador": resultado.getValorJogador(),
                "valorDealer": resultado.getValorDealer(),
                "lucro": resultado.getLucro(),
                "dataHora": resultado.getDataHora()
            }
            for resultado in reversed(resultados)
        ]

    def __estadoExpirado(self, sala, idUsuario):
        return {
            "sala": self.__dictSala(sala),
            "fase": "expirada",
            "segundosRestantes": 0,
            "idRodada": None,
            "jogadores": [],
            "meu": None,
            "minhasAcoes": [],
            "turno": {"idJogador": None, "nome": None},
            "resultados": None,
            "participantes": [],
            "presenca": [],
            "dealer": {"cartas": [], "valoresParciais": [], "valor": 0, "valorFinal": 0, "revelado": False},
            "historico": [],
            "chat": [],
            "mensagem": "Esta sala expirou. Crie uma nova para jogar com os amigos.",
            "expirada": True
        }

    # ------------------------------------------------------------- apoio

    def __sala(self, codigo):
        self.__limparSalasExpiradas(agoraBrasiliaData())
        sala = self.__salaRepo.consultarPorCodigo(codigo)

        if sala is None:
            raise Exception("Sala não encontrada. O link pode estar errado ou a sala já foi encerrada.")

        return sala

    def __limparSalasExpiradas(self, agora):
        limite = agora - timedelta(minutes=GRACA_EXPIRACAO_MINUTOS)

        for sala in self.__salaRepo.consultarExpiradas(limite):
            self.__rodadaRepo.deletarPorSala(sala.getId())
            self.__salaRepo.deletar(sala.getId())
            chatSessao.limpar(sala.getCodigo())
            presencaMesa.limpar(sala.getCodigo())

    def __nomeDe(self, idUsuario):
        if idUsuario is None:
            return None

        usuario = self.__usuarioRepo.consultaPorId(int(idUsuario))
        return usuario.getUsuario() if usuario else None

    def __validarValor(self, valor):
        try:
            numero = round(float(valor), 2)
        except (TypeError, ValueError):
            raise Exception("Valor da aposta precisa ser um número")

        if numero < APOSTA_MINIMA:
            raise Exception(f"Aposta mínima é {self.__formatar(APOSTA_MINIMA)}")

        if numero > APOSTA_MAXIMA:
            raise Exception(f"Aposta máxima é {self.__formatar(APOSTA_MAXIMA)}")

        return numero

    @staticmethod
    def __descricaoComando(comando):
        return {
            "comprar": "comprou uma carta",
            "parar": "parou",
            "dobrar": "dobrou a aposta",
            "dividir": "dividiu a mão"
        }.get(comando, comando)

    @staticmethod
    def __converterId(idUsuario):
        if idUsuario is None:
            return None

        try:
            return int(idUsuario)
        except (TypeError, ValueError):
            raise Exception("Usuário inválido")

    @staticmethod
    def __dictSala(sala):
        if sala is None:
            return None

        dados = sala.getDict()
        dados["segundosRestantes"] = sala.segundosRestantes(agoraBrasiliaData())
        dados["duracaoMinutos"] = DURACAO_SALA_MINUTOS

        return dados

    @staticmethod
    def __formatar(valor):
        return f"R$ {valor:,.2f}".replace(",", "TEMP").replace(".", ",").replace("TEMP", ".")
