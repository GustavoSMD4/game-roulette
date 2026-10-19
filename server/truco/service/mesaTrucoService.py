import random
import threading
import uuid
from datetime import timedelta

from server.games import truco as regras
from server.roulette.service import chatSessao, presencaMesa
from server.truco.repository.partidaTrucoRepo import PartidaTrucoRepo
from server.truco.repository.salaTrucoRepo import SalaTrucoRepo
from server.usuario.repository.usuarioRepo import UsuarioRepo
from utils import agoraBrasiliaData

# Mesa ao vivo de truco mineiro: 20 segundos por jogada e 20 para responder um truco
DURACAO_JOGADA = 20
DURACAO_RESPOSTA = 20
DURACAO_VAZA = 4
DURACAO_RESULTADO = 8

DURACAO_SALA_MINUTOS = 60
GRACA_EXPIRACAO_MINUTOS = 10
LIMITE_HISTORICO = 6
CARTAS_POR_MAO = 3

ACOES_TRUCO = ("pedir", "aceitar", "correr")

# O Flask atende em varias threads e o SQLite tem um escritor por vez: serializa o avanco da mesa
CADEADO_MESA = threading.Lock()


class MesaTrucoService:
    """Truco mineiro ao vivo em sala privada (1x1 ou 2x2).

    O relogio anda o jogo (sem timers de fundo): cada requisicao verifica se o tempo da jogada
    venceu, se alguem nao respondeu o truco e se a mao terminou. A partida inteira fica em JSON,
    entao todos veem a mesma mesa e recarregar a pagina nao muda nada.
    """

    def __init__(self, salaRepo: SalaTrucoRepo, partidaRepo: PartidaTrucoRepo, usuarioRepo: UsuarioRepo):
        self.__salaRepo = salaRepo
        self.__partidaRepo = partidaRepo
        self.__usuarioRepo = usuarioRepo

    @classmethod
    def newService(cls):
        return cls(SalaTrucoRepo.newRepo(), PartidaTrucoRepo.newRepo(), UsuarioRepo.newRepo())

    # ------------------------------------------------------------- sala

    def criarSala(self, req: dict):
        idUsuario = self.__converterId(req.get("idUsuario"))
        usuario = self.__usuarioRepo.consultaPorId(idUsuario) if idUsuario is not None else None

        if usuario is None:
            raise Exception("Usuário não encontrado")

        modo = str(req.get("modo") or "2x2").strip().lower()

        if modo not in ("1x1", "2x2"):
            raise Exception("Escolha o modo da mesa: 1x1 ou 2x2")

        agora = agoraBrasiliaData()
        nome = str(req.get("nome") or "").strip() or f"Truco de {usuario.getUsuario()}"

        with CADEADO_MESA:
            self.__limparSalasExpiradas(agora)
            sala = self.__salaRepo.criar(nome[:60], modo, usuario.getId(), agora,
                                         agora + timedelta(minutes=DURACAO_SALA_MINUTOS))
            estado = self.__novoEstado(sala)
            self.__assentar(estado, usuario)
            self.__partidaRepo.criar(sala.getId(), "esperando", agora,
                                     agora + timedelta(minutes=DURACAO_SALA_MINUTOS), estado)

        return {
            "sala": self.__dictSala(sala),
            "mensagem": f"Sala {modo} criada! O link vale por {DURACAO_SALA_MINUTOS} minutos."
        }

    def entrar(self, req: dict):
        """Senta o jogador na mesa (o criador ja entra sentado)."""
        idUsuario = self.__converterId(req.get("idUsuario"))
        usuario = self.__usuarioRepo.consultaPorId(idUsuario) if idUsuario is not None else None

        if usuario is None:
            raise Exception("Usuário não encontrado")

        with CADEADO_MESA:
            sala = self.__sala(req.get("codigo"))
            partida = self.__avancar(self.__partidaAtual(sala), agoraBrasiliaData())

            if partida.getFase() != "esperando":
                raise Exception("Esta partida já começou. Espere a próxima para entrar.")

            estado = partida.getEstado()
            self.__assentar(estado, usuario)
            partida = self.__salvar(partida.getId(), "esperando", partida.getDataHoraFimFase(), estado)

        return self.__montarEstado(sala, partida, idUsuario, req.get("desdeChat", 0))

    def novaPartida(self, req: dict):
        idUsuario = self.__converterId(req.get("idUsuario"))

        with CADEADO_MESA:
            sala = self.__sala(req.get("codigo"))
            agora = agoraBrasiliaData()
            partida = self.__avancar(self.__partidaAtual(sala), agora)

            if partida.getFase() != "fim":
                raise Exception("A partida ainda está em andamento")

            estado = partida.getEstado()
            estado["pontos"] = {"A": 0, "B": 0}
            estado["maosGanhas"] = {"A": 0, "B": 0}
            estado["numeroMao"] = 0
            estado["mao"] = None
            estado["resultado"] = None
            estado["historico"] = []
            estado["mensagem"] = "Nova partida! Quem perder leva."
            partida = self.__salvar(partida.getId(), "esperando",
                                    agora + timedelta(minutes=DURACAO_SALA_MINUTOS), estado)
            partida = self.__avancar(partida, agora)

        return self.__montarEstado(sala, partida, idUsuario, req.get("desdeChat", 0))

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

    # ------------------------------------------------------------- jogadas

    def estado(self, req: dict = None):
        req = req or {}
        idUsuario = self.__converterId(req.get("idUsuario"))

        with CADEADO_MESA:
            sala = self.__sala(req.get("codigo"))
            agora = agoraBrasiliaData()

            if sala.isExpirada(agora):
                return self.__estadoExpirado(sala)

            self.__limparSalasExpiradas(agora)
            partida = self.__avancar(self.__partidaAtual(sala), agora)

        return self.__montarEstado(sala, partida, idUsuario, req.get("desdeChat", 0))

    def jogar(self, req: dict):
        """Joga uma carta: por id (mão normal) ou por posição (mão de ferro, tudo virado)."""
        idUsuario = self.__converterId(req.get("idUsuario"))

        if idUsuario is None:
            raise Exception("Usuário inválido")

        with CADEADO_MESA:
            sala = self.__sala(req.get("codigo"))
            agora = agoraBrasiliaData()

            if sala.isExpirada(agora):
                raise Exception("Esta sala já expirou. Crie uma nova para jogar com os amigos.")

            partida = self.__avancar(self.__partidaAtual(sala), agora)

            if partida.getFase() != "jogando":
                raise Exception("Não há mão em andamento")

            estado = partida.getEstado()
            mao = estado.get("mao")

            if mao is None or mao.get("finalizada"):
                raise Exception("Esta mão já acabou")

            if mao.get("pedido") and mao["pedido"].get("aceito") is None:
                raise Exception("Espere a resposta do truco")

            idJogador = str(idUsuario)

            if idJogador not in estado["assentos"]:
                raise Exception("Você não está nesta mesa")

            if self.__jogadorDoTurno(estado) != idJogador:
                raise Exception(f"Não é a sua vez. Agora é a vez de {self.__nomeDe(self.__jogadorDoTurno(estado))}.")

            cartas = mao["maos"].get(idJogador) or []

            if not cartas:
                raise Exception("Você não tem cartas na mão")

            if mao.get("vazaFechada"):
                raise Exception("A vaza acabou de fechar. Espere a próxima para jogar.")

            indice = self.__escolherCarta(mao, cartas, req)

            if not self.__jogarCarta(estado, idJogador, indice):
                raise Exception("Não foi possível jogar essa carta")

            if mao["finalizada"]:
                partida = self.__finalizarMao(partida, agora)
            else:
                # fechou a vaza: deixa ela na mesa antes de abrir a proxima
                pausa = DURACAO_VAZA if mao.get("vazaFechada") else DURACAO_JOGADA
                partida = self.__salvar(partida.getId(), "jogando",
                                        agora + timedelta(seconds=pausa), estado)

        return self.__montarEstado(sala, partida, idUsuario, req.get("desdeChat", 0))

    def truco(self, req: dict):
        """Pedir truco, aceitar ou correr."""
        idUsuario = self.__converterId(req.get("idUsuario"))
        acao = str(req.get("acao") or "").strip().lower()

        if idUsuario is None:
            raise Exception("Usuário inválido")

        if acao not in ACOES_TRUCO:
            raise Exception("Ação de truco inválida")

        with CADEADO_MESA:
            sala = self.__sala(req.get("codigo"))
            agora = agoraBrasiliaData()

            if sala.isExpirada(agora):
                raise Exception("Esta sala já expirou. Crie uma nova para jogar com os amigos.")

            partida = self.__avancar(self.__partidaAtual(sala), agora)

            if partida.getFase() != "jogando":
                raise Exception("Não há mão em andamento")

            estado = partida.getEstado()
            mao = estado.get("mao")
            idJogador = str(idUsuario)

            if idJogador not in estado["assentos"]:
                raise Exception("Você não está nesta mesa")

            if acao == "pedir":
                self.__pedirTruco(estado, idJogador)
                partida = self.__salvar(partida.getId(), "jogando",
                                        agora + timedelta(seconds=DURACAO_RESPOSTA), estado)
            else:
                self.__responderTruco(estado, acao, idJogador)

                if mao["finalizada"]:
                    partida = self.__finalizarMao(partida, agora)
                else:
                    partida = self.__salvar(partida.getId(), "jogando",
                                            agora + timedelta(seconds=DURACAO_JOGADA), estado)

        return self.__montarEstado(sala, partida, idUsuario, req.get("desdeChat", 0))

    # ------------------------------------------------------------- relogio da mesa

    def __partidaAtual(self, sala):
        partida = self.__partidaRepo.consultarAtual(sala.getId())

        if partida is None:
            agora = agoraBrasiliaData()
            partida = self.__partidaRepo.criar(sala.getId(), "esperando",
                                               agora + timedelta(minutes=DURACAO_SALA_MINUTOS),
                                               agora + timedelta(minutes=DURACAO_SALA_MINUTOS),
                                               self.__novoEstado(sala))

        return partida

    def __avancar(self, partida, agora):
        fase = partida.getFase()

        if fase == "fim":
            return partida

        if fase == "esperando":
            estado = partida.getEstado()

            if len(estado.get("assentos") or []) < estado.get("jogadoresPorMesa", 4):
                return partida

            return self.__iniciarMao(partida, agora)

        if fase == "jogando":
            return self.__andarJogo(partida, agora)

        if agora < partida.getDataHoraFimFase():
            return partida

        return self.__iniciarMao(partida, agora)

    def __andarJogo(self, partida, agora):
        """Resolve o que venceu pelo relogio: resposta do truco e jogada de quem travou."""
        for _ in range(96):
            estado = partida.getEstado()
            mao = estado.get("mao")

            if mao is None:
                return self.__iniciarMao(partida, agora)

            if mao.get("finalizada"):
                return self.__finalizarMao(partida, agora)

            if agora < partida.getDataHoraFimFase():
                return partida

            if mao.get("vazaFechada"):
                # pausa da vaza: as cartas e quem levou ficam na mesa antes de seguir
                if regras.maoDecidida(mao["vazas"]):
                    return self.__finalizarMao(partida, agora)

                self.__abrirProximaVaza(estado)
                partida = self.__salvar(partida.getId(), "jogando",
                                        agora + timedelta(seconds=DURACAO_JOGADA), estado)
                agora = agoraBrasiliaData()
                continue

            pendente = bool(mao.get("pedido")) and mao["pedido"].get("aceito") is None

            if pendente:
                self.__responderTruco(estado, "aceitar", automatico=True)
                fimFase = agora + timedelta(seconds=DURACAO_JOGADA)
                estado["mensagem"] = "O tempo de resposta acabou: o truco foi aceito automaticamente."
            else:
                idJogador = self.__jogadorDoTurno(estado)
                cartas = mao["maos"].get(idJogador) or []

                if cartas:
                    self.__jogarCarta(estado, idJogador, random.randrange(len(cartas)), automatico=True)

                if mao.get("finalizada"):
                    return self.__finalizarMao(partida, agora)

                if mao.get("vazaFechada"):
                    partida = self.__salvar(partida.getId(), "jogando",
                                            agora + timedelta(seconds=DURACAO_VAZA), estado)
                    agora = agoraBrasiliaData()
                    continue

                fimFase = agora + timedelta(seconds=DURACAO_JOGADA)

            partida = self.__salvar(partida.getId(), "jogando", fimFase, estado)
            agora = agoraBrasiliaData()

        return partida

    def __iniciarMao(self, partida, agora):
        estado = partida.getEstado()
        assentos = estado.get("assentos") or []

        if len(assentos) < estado.get("jogadoresPorMesa", 4):
            return partida

        estado["numeroMao"] = int(estado.get("numeroMao") or 0) + 1

        pontos = estado.get("pontos") or {"A": 0, "B": 0}
        tipo = regras.tipoDaMao(pontos.get("A", 0), pontos.get("B", 0))
        valor = regras.valorInicial(tipo)
        semente = uuid.uuid4().int % 1000000000
        baralho = regras.baralhoLimpo(semente)
        maos = {}
        usadas = 0

        for idJogador in assentos:
            maos[str(idJogador)] = baralho[usadas:usadas + CARTAS_POR_MAO]
            usadas += CARTAS_POR_MAO

        abriu = (estado["numeroMao"] - 1) % len(assentos)

        estado["mao"] = {
            "numero": estado["numeroMao"],
            "tipo": tipo,
            "valorBase": valor,
            "valor": valor,
            "ferro": tipo == "ferro",
            "semente": semente,
            "usadas": usadas,
            "maos": maos,
            "abriu": abriu,
            "turno": abriu,
            "vazaAtual": 1,
            "vaza": {"numero": 1, "jogadas": [], "vencedor": None, "ganhador": None},
            "vazas": [],
            "vazaFechada": False,
            "pedido": None,
            "pediu": None,
            "finalizada": False,
            "vencedor": None,
            "valorGanho": 0,
            "desistiu": None,
            "revelada": False
        }
        estado["resultado"] = None
        estado["mensagem"] = self.__mensagemInicio(tipo, valor)

        return self.__salvar(partida.getId(), "jogando", agora + timedelta(seconds=DURACAO_JOGADA), estado)

    def __finalizarMao(self, partida, agora):
        estado = partida.getEstado()
        mao = estado.get("mao")

        if mao is None:
            return partida

        equipes = self.__equipePorJogador(estado)
        equipeMao = equipes.get(str(estado["assentos"][mao["abriu"]]))
        vencedor = mao.get("vencedor")
        valor = mao.get("valorGanho")

        if vencedor is None:
            vencedor = regras.vencedorDaMao([vaza.get("vencedor") for vaza in mao["vazas"]], equipeMao)
            valor = mao["valor"]
            mao["vencedor"] = vencedor
            mao["valorGanho"] = valor
            mao["empate"] = all(vaza.get("vencedor") is None for vaza in mao["vazas"]) if mao["vazas"] else False

        mao["finalizada"] = True
        mao["revelada"] = True
        estado["pontos"][vencedor] = int(estado["pontos"].get(vencedor, 0)) + int(valor)
        estado["maosGanhas"][vencedor] = int(estado["maosGanhas"].get(vencedor, 0)) + 1
        fim = estado["pontos"][vencedor] >= regras.PONTOS_PARTIDA

        estado["resultado"] = {
            "numero": mao["numero"],
            "tipo": mao["tipo"],
            "valor": valor,
            "vencedor": vencedor,
            "desistiu": mao.get("desistiu"),
            "empate": bool(mao.get("empate")),
            "vazasJogadas": len(mao["vazas"]),
            "pontos": dict(estado["pontos"]),
            "fim": fim
        }
        estado["historico"] = ([{
            "numero": mao["numero"],
            "tipo": mao["tipo"],
            "valor": valor,
            "vencedor": vencedor
        }] + list(estado.get("historico") or []))[:LIMITE_HISTORICO]

        estado["mensagem"] = self.__mensagemFim(estado["resultado"])

        return self.__salvar(partida.getId(), "fim" if fim else "resultado",
                             agora + timedelta(seconds=DURACAO_RESULTADO), estado)

    # ------------------------------------------------------------- cartas

    @staticmethod
    def __escolherCarta(mao, cartas, req):
        idCarta = req.get("carta")
        indice = req.get("indice")

        if idCarta:
            for posicao, carta in enumerate(cartas):
                if str(carta.get("id")) == str(idCarta):
                    return posicao

            raise Exception("Essa carta não está mais na sua mão")

        try:
            posicao = int(indice)
        except (TypeError, ValueError):
            raise Exception("Escolha uma carta para jogar")

        if 0 <= posicao < len(cartas):
            return posicao

        raise Exception("Escolha uma das suas cartas")

    def __jogarCarta(self, estado, idJogador, indice, automatico=False):
        """Tira a carta da mão, joga na vaza e passa a vez (ou fecha a vaza). Retorna se jogou."""
        mao = estado["mao"]
        idJogador = str(idJogador)
        cartas = mao["maos"].get(idJogador) or []

        if not (0 <= indice < len(cartas)):
            return False

        carta = cartas.pop(indice)
        mao["vaza"]["jogadas"].append({
            "idJogador": idJogador,
            "nome": self.__nomeDe(idJogador),
            "carta": carta,
            "automatica": bool(automatico)
        })

        if len(mao["vaza"]["jogadas"]) >= len(estado["assentos"]):
            self.__fecharVaza(estado)
        else:
            mao["turno"] = (mao["turno"] + 1) % len(estado["assentos"])

        return True

    def __fecharVaza(self, estado):
        """Fecha a vaza e deixa ela na mesa por alguns segundos, com quem levou destacado."""
        mao = estado["mao"]
        vaza = mao["vaza"]
        equipes = self.__equipePorJogador(estado)
        vencedor = regras.vencedorDaVaza(vaza["jogadas"], equipes)
        ganhador = self.__ganhadorDaVaza(vaza, equipes, vencedor)
        vaza["vencedor"] = vencedor
        vaza["ganhador"] = ganhador
        mao["vazas"].append(vaza)
        mao["vazaFechada"] = True
        mao["turno"] = mao["abriu"]

        if ganhador:
            carta = next((jogada["carta"] for jogada in vaza["jogadas"]
                          if str(jogada["idJogador"]) == str(ganhador)), None)
            estado["mensagem"] = (f"{vaza['numero']}ª vaza: {self.__nomeDe(ganhador)} levou com " +
                                  (self.__nomeDaCarta(carta) if carta else "a carta mais forte") + ".")
        else:
            estado["mensagem"] = f"{vaza['numero']}ª vaza empatou: ninguém levou."

        if regras.maoDecidida(mao["vazas"]):
            equipe = regras.vencedorDaMao([item.get("vencedor") for item in mao["vazas"]],
                                          equipes.get(str(estado["assentos"][mao["abriu"]])))
            estado["mensagem"] += (f" A mão está decidida: {self.__nomesDaEquipe(estado, equipe)} "
                                   "não precisa das cartas restantes.")

    def __abrirProximaVaza(self, estado):
        """Quem ganhou a vaza abre a seguinte; se empatou, quem abriu continua abrindo."""
        mao = estado["mao"]
        ultima = mao["vazas"][-1] if mao["vazas"] else None

        if ultima and ultima.get("ganhador") in (estado.get("assentos") or []):
            mao["abriu"] = estado["assentos"].index(ultima["ganhador"])

        mao["vazaFechada"] = False
        mao["vazaAtual"] = len(mao["vazas"]) + 1
        mao["vaza"] = {"numero": mao["vazaAtual"], "jogadas": [], "vencedor": None, "ganhador": None}
        mao["turno"] = mao["abriu"]

    @staticmethod
    def __ganhadorDaVaza(vaza, equipes, vencedor):
        """Jogador dono da carta mais forte do time que levou a vaza."""
        if vencedor is None:
            return None

        doTime = [jogada for jogada in vaza["jogadas"] if equipes.get(str(jogada["idJogador"])) == vencedor]

        if not doTime:
            return None

        return str(max(doTime, key=lambda jogada: regras.forcaDaCarta(jogada["carta"]))["idJogador"])

    # ------------------------------------------------------------- truco

    def __pedirTruco(self, estado, idJogador):
        mao = estado["mao"]
        equipes = self.__equipePorJogador(estado)
        minhaEquipe = equipes.get(idJogador)
        daVez = self.__jogadorDoTurno(estado)

        if mao.get("finalizada"):
            raise Exception("Esta mão já acabou")

        if mao.get("vazaFechada"):
            raise Exception("A vaza acabou de fechar. Espere a próxima para pedir truco.")

        if mao.get("pedido") and mao["pedido"].get("aceito") is None:
            raise Exception("Já existe um truco esperando resposta")

        if equipes.get(daVez) != minhaEquipe:
            raise Exception("Só quem está na vez pode pedir truco")

        if mao.get("pediu") == minhaEquipe:
            raise Exception("Quem pediu o truco espera o outro time pedir de volta")

        proximo = regras.permiteTruco(mao["tipo"], mao["valor"])

        if proximo is None:
            if mao["tipo"] == "ferro":
                raise Exception("Mão de ferro não tem truco")
            if mao["tipo"] in ("dez", "doze"):
                raise Exception("Mão de dez não tem truco")
            raise Exception("Não dá para aumentar mais esta mão")

        mao["pedido"] = {
            "equipe": minhaEquipe,
            "valor": proximo,
            "anterior": mao["valor"],
            "por": idJogador,
            "porNome": self.__nomeDe(idJogador)
        }
        estado["mensagem"] = f"{self.__nomeDe(idJogador)} pediu {self.__nomeDoPedido(proximo)}!"

    def __responderTruco(self, estado, acao, idJogador=None, automatico=False):
        mao = estado["mao"]
        pedido = mao.get("pedido")

        if not pedido:
            raise Exception("Não há truco para responder")

        equipes = self.__equipePorJogador(estado)
        minhaEquipe = equipes.get(idJogador) if idJogador else None

        if not automatico and minhaEquipe is None:
            raise Exception("Você não está nesta mesa")

        if not automatico and minhaEquipe == pedido["equipe"]:
            raise Exception("Quem pediu o truco não responde: espere o outro time")

        pedido["aceito"] = acao == "aceitar"

        if pedido["aceito"]:
            mao["valor"] = pedido["valor"]
            mao["pediu"] = pedido["equipe"]
            mao["pedido"] = None
            estado["mensagem"] = f"Truco aceito! Esta mão agora vale {mao['valor']} pontos."
            return

        # correu: quem pediu leva a mão pelo valor que estava valendo antes do aumento
        mao["vencedor"] = pedido["equipe"]
        mao["valorGanho"] = pedido["anterior"]
        mao["desistiu"] = equipes.get(str(idJogador)) if idJogador else self.__outraEquipe(pedido["equipe"])
        mao["finalizada"] = True
        mao["revelada"] = True
        estado["mensagem"] = (f"{self.__outraEquipe(pedido['equipe'])} correu do truco: "
                              f"{pedido['equipe']} leva a mão valendo {pedido['anterior']}.")

    # ------------------------------------------------------------- apoio

    def __novoEstado(self, sala):
        return {
            "modo": sala.getModo(),
            "jogadoresPorMesa": sala.getJogadoresPorMesa(),
            "assentos": [],
            "pontos": {"A": 0, "B": 0},
            "maosGanhas": {"A": 0, "B": 0},
            "numeroMao": 0,
            "mao": None,
            "resultado": None,
            "historico": [],
            "mensagem": "Mesa criada! Mande o link para os jogadores entrarem."
        }

    def __assentar(self, estado, usuario):
        idJogador = str(usuario.getId())

        if idJogador in estado["assentos"]:
            return

        if len(estado["assentos"]) >= estado["jogadoresPorMesa"]:
            raise Exception(f"A mesa está cheia ({estado['jogadoresPorMesa']} jogadores)")

        estado["assentos"].append(idJogador)
        entrou = len(estado["assentos"])
        estado["mensagem"] = (f"{usuario.getUsuario()} entrou na mesa "
                             f"({entrou}/{estado['jogadoresPorMesa']}). " +
                             ("Cartas na mesa!" if entrou >= estado["jogadoresPorMesa"]
                              else "Aguardando os outros jogadores..."))

    @staticmethod
    def __equipePorJogador(estado):
        return {
            str(idJogador): regras.EQUIPES[posicao % 2]
            for posicao, idJogador in enumerate(estado.get("assentos") or [])
        }

    @staticmethod
    def __outraEquipe(equipe):
        return "B" if equipe == "A" else "A"

    def __jogadorDoTurno(self, estado):
        mao = estado.get("mao")

        if not mao or not estado.get("assentos") or mao.get("finalizada") or mao.get("vazaFechada"):
            return None

        return str(estado["assentos"][mao["turno"] % len(estado["assentos"])])

    @staticmethod
    def __mensagemInicio(tipo, valor):
        if tipo == "ferro":
            return "MÃO DE FERRO! Os dois times estão com 10: as cartas vêm viradas para baixo e ninguém vê nada."

        if tipo == "dez":
            return "Mão de dez! Quem está com 10 pontos não pode pedir truco. Esta mão vale 10."

        if tipo == "doze":
            return "Mão de doze! Esta mão vale 12 e decide a partida."

        return f"Cartas dadas! Esta mão vale {valor}."

    @staticmethod
    def __mensagemFim(resultado):
        if resultado.get("desistiu"):
            return (f"Time {resultado['vencedor']} levou a mão valendo {resultado['valor']} "
                    f"(o outro time correu).")

        if resultado.get("empate"):
            return (f"As vazas empataram: quem era mão levou "
                    f"{resultado['valor']} ponto(s).")

        if resultado.get("fim"):
            return f"Fim de jogo! Time {resultado['vencedor']} ganhou a partida."

        extra = " em duas vazas" if resultado.get("vazasJogadas") == 2 else ""

        return (f"Time {resultado['vencedor']} levou a mão{extra} valendo "
                f"{resultado['valor']} pontos.")

    @staticmethod
    def __nomeDoPedido(valor):
        return {4: "truco", 8: "retruco"}.get(int(valor), f"vale {int(valor)}")

    NOMES_RANK = {"ace": "A", "jack": "J", "queen": "Q", "king": "K"}
    NOMES_NAIPE = {"spades": "espadas", "hearts": "copas", "clubs": "paus", "diamonds": "ouros"}

    @classmethod
    def __nomeDaCarta(cls, carta):
        if not carta:
            return None

        rank = cls.NOMES_RANK.get(carta.get("rank"), carta.get("rank"))
        return f"{rank} de {cls.NOMES_NAIPE.get(carta.get('suit'), carta.get('suit'))}"

    def __nomesDaEquipe(self, estado, equipe):
        equipes = self.__equipePorJogador(estado)
        nomes = [self.__nomeDe(idJogador) for idJogador, time in equipes.items() if time == equipe]

        return " e ".join(nome for nome in nomes if nome) or f"Time {equipe}"

    def __nomeDe(self, idJogador):
        if idJogador is None:
            return None

        usuario = self.__usuarioRepo.consultaPorId(int(idJogador))
        return usuario.getUsuario() if usuario else None

    def __sala(self, codigo):
        self.__limparSalasExpiradas(agoraBrasiliaData())
        sala = self.__salaRepo.consultarPorCodigo(codigo)

        if sala is None:
            raise Exception("Sala não encontrada. O link pode estar errado ou a sala já foi encerrada.")

        return sala

    def __limparSalasExpiradas(self, agora):
        limite = agora - timedelta(minutes=GRACA_EXPIRACAO_MINUTOS)

        for sala in self.__salaRepo.consultarExpiradas(limite):
            self.__partidaRepo.deletarPorSala(sala.getId())
            self.__salaRepo.deletar(sala.getId())
            chatSessao.limpar(sala.getCodigo())
            presencaMesa.limpar(sala.getCodigo())

    def __salvar(self, idPartida, fase, fimFase, estado, mensagem=None):
        if mensagem is not None:
            estado["mensagem"] = mensagem

        return self.__partidaRepo.atualizar(idPartida, fase, fimFase, estado)

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
        return dados

    def __estadoExpirado(self, sala):
        return {
            "expirada": True,
            "sala": self.__dictSala(sala),
            "fase": "expirada",
            "mensagem": "Esta sala privada chegou ao fim de uma hora.",
            "jogadores": [],
            "minhasCartas": [],
            "pontos": {"A": 0, "B": 0},
            "chat": [],
            "presenca": []
        }

    # ------------------------------------------------------------- resposta

    def __montarEstado(self, sala, partida, idUsuario, desdeChat=0):
        estado = partida.getEstado()
        presencaMesa.marcar(sala.getCodigo(), idUsuario, self.__nomeDe(idUsuario))
        presentes = presencaMesa.presentes(sala.getCodigo())
        assentos = [str(item) for item in (estado.get("assentos") or [])]
        equipes = self.__equipePorJogador(estado)
        minhaEquipe = equipes.get(str(idUsuario))
        fase = partida.getFase()
        mao = estado.get("mao")
        revelar = fase in ("resultado", "fim")
        pendente = bool(mao and mao.get("pedido") and mao["pedido"].get("aceito") is None)
        daVez = self.__jogadorDoTurno(estado) if mao and not mao.get("finalizada") and not pendente else None
        vencedores = self.__vazasVencidas(mao, equipes)

        jogadores = []

        for posicao, idJogador in enumerate(assentos):
            jogadores.append({
                "idJogador": idJogador,
                "nome": self.__nomeDe(idJogador),
                "posicao": posicao,
                "equipe": equipes.get(idJogador),
                "eu": idJogador == str(idUsuario),
                "parceiro": bool(minhaEquipe) and equipes.get(idJogador) == minhaEquipe and idJogador != str(idUsuario),
                "naVez": idJogador == daVez,
                "cartas": self.__cartasVisiveis(mao, idJogador, idUsuario, revelar),
                "vazasGanhas": vencedores.get(idJogador, 0)
            })

        return {
            "sala": self.__dictSala(sala),
            "fase": fase,
            "segundosRestantes": partida.segundosRestantes(agoraBrasiliaData()),
            "mensagem": estado.get("mensagem"),
            "modo": estado.get("modo"),
            "jogadoresPorMesa": estado.get("jogadoresPorMesa"),
            "assentosOcupados": len(assentos),
            "pontos": estado.get("pontos") or {"A": 0, "B": 0},
            "maosGanhas": estado.get("maosGanhas") or {"A": 0, "B": 0},
            "numeroMao": estado.get("numeroMao"),
            "tipoMao": mao.get("tipo") if mao else None,
            "valorMao": mao.get("valor") if mao else None,
            "ferro": bool(mao and mao.get("ferro")),
            "minhaEquipe": minhaEquipe,
            "nomesEquipes": self.__nomesEquipes(assentos, equipes),
            "jogadores": jogadores,
            "minhasCartas": self.__cartasVisiveis(mao, str(idUsuario), idUsuario, revelar) if str(idUsuario) in assentos else [],
            "minhaVez": bool(daVez) and daVez == str(idUsuario),
            "vazaAtual": mao.get("vazaAtual") if mao else None,
            "vaza": mao.get("vaza") if mao else None,
            "vazaFechada": bool(mao and mao.get("vazaFechada")),
            "maoDecidida": bool(mao and regras.maoDecidida(mao.get("vazas") or [])),
            "vazasJogadas": len((mao or {}).get("vazas") or []),
            "vazas": (mao or {}).get("vazas") or [],
            "pedido": self.__dictPedido(mao, minhaEquipe) if pendente else None,
            "acoes": self.__acoes(estado, mao, idUsuario, minhaEquipe, pendente, daVez, fase),
            "turno": {
                "idJogador": daVez,
                "nome": self.__nomeDe(daVez) if daVez else None,
                "equipe": equipes.get(daVez) if daVez else None,
                "eu": bool(daVez) and daVez == str(idUsuario)
            },
            "resultado": self.__dictResultado(estado.get("resultado"), minhaEquipe),
            "historico": estado.get("historico") or [],
            "presenca": presentes,
            "chat": chatSessao.novas(sala.getCodigo(), desdeChat)
        }

    def __cartasVisiveis(self, mao, idJogador, idUsuario, revelar):
        """Mostra as cartas de quem pediu (e de todos, quando a mão acaba).

        Na mão de ferro ninguém vê carta nenhuma: só posições viradas para baixo.
        """
        if not mao:
            return []

        cartas = mao["maos"].get(str(idJogador)) or []
        escondidas = bool(mao.get("ferro")) and not revelar

        if escondidas or (str(idJogador) != str(idUsuario) and not revelar):
            return [{"indice": indice, "oculta": True, "carta": None} for indice in range(len(cartas))]

        return [{"indice": indice, "oculta": False, "carta": carta} for indice, carta in enumerate(cartas)]

    @staticmethod
    def __vazasVencidas(mao, equipes):
        """Quantas vazas cada jogador ganhou (conta as vazas do time dele)."""
        porEquipe = {}

        for vaza in (mao or {}).get("vazas") or []:
            vencedor = vaza.get("vencedor")

            if vencedor:
                porEquipe[vencedor] = porEquipe.get(vencedor, 0) + 1

        return {idJogador: porEquipe.get(equipe, 0) for idJogador, equipe in equipes.items()}

    def __nomesEquipes(self, assentos, equipes):
        nomes = {"A": [], "B": []}

        for idJogador in assentos:
            equipe = equipes.get(idJogador)
            nome = self.__nomeDe(idJogador)

            if equipe and nome:
                nomes[equipe].append(nome)

        return nomes

    @staticmethod
    def __dictPedido(mao, minhaEquipe):
        pedido = mao["pedido"]

        return {
            "equipe": pedido["equipe"],
            "valor": pedido["valor"],
            "anterior": pedido["anterior"],
            "porNome": pedido.get("porNome"),
            "meu": pedido["equipe"] == minhaEquipe,
            "podeResponder": pedido["equipe"] != minhaEquipe
        }

    @staticmethod
    def __acoes(estado, mao, idUsuario, minhaEquipe, pendente, daVez, fase):
        podePedir = False
        proximo = None
        podeResponder = False
        valorResponder = None

        if mao and not mao.get("finalizada") and fase == "jogando" and minhaEquipe:
            if pendente:
                pedido = mao["pedido"]
                podeResponder = pedido["equipe"] != minhaEquipe
                valorResponder = pedido["anterior"]
            else:
                proximo = regras.permiteTruco(mao["tipo"], mao["valor"])
                podePedir = bool(
                    proximo is not None
                    and MesaTrucoService.__equipeDoJogador(estado, daVez) == minhaEquipe
                    and mao.get("pediu") != minhaEquipe
                )

        return {
            "podeJogar": bool(daVez) and daVez == str(idUsuario),
            "podePedirTruco": podePedir,
            "proximoValor": proximo,
            "podeResponder": podeResponder,
            "valorResponder": valorResponder
        }

    @staticmethod
    def __equipeDoJogador(estado, idJogador):
        assentos = [str(item) for item in (estado.get("assentos") or [])]

        if idJogador is None or str(idJogador) not in assentos:
            return None

        return regras.EQUIPES[assentos.index(str(idJogador)) % 2]

    @staticmethod
    def __dictResultado(resultado, minhaEquipe):
        if not resultado:
            return None

        dados = dict(resultado)
        dados["minhaEquipe"] = minhaEquipe
        dados["ganhei"] = resultado.get("vencedor") == minhaEquipe
        return dados
