import threading
from datetime import timedelta

from server.games.roulette import Roulette
from server.roulette.models.apostaRoletaModel import ApostaRoleta
from server.roulette.models.resultadoRoletaModel import ResultadoRoleta
from server.roulette.repository.apostaRoletaRepo import ApostaRoletaRepo
from server.roulette.repository.rodadaRoletaRepo import RodadaRoletaRepo
from server.roulette.repository.resultadoRoletaRepo import ResultadoRoletaRepo
from server.roulette.repository.sessaoRoletaRepo import SessaoRoletaRepo
from server.roulette.service import chatSessao, presencaMesa
from server.usuario.repository.usuarioRepo import UsuarioRepo
from utils import agoraBrasilia, agoraBrasiliaData

# Ciclo da mesa: janela de apostas -> roleta girando -> resultado na tela -> recomeça
DURACAO_APOSTA = 20
DURACAO_GIRO = 5
DURACAO_RESULTADO = 7
DURACAO_CICLO = DURACAO_APOSTA + DURACAO_GIRO + DURACAO_RESULTADO

# Mesas privadas: validade do link de convite e quanto tempo a sessão fica guardada após expirar
DURACAO_SESSAO_MINUTOS = 60
GRACA_EXPIRACAO_MINUTOS = 10

APOSTA_MINIMA = 1.0
APOSTA_MAXIMA = 1000.0

# O Flask responde em várias threads e o SQLite aceita um escritor por vez:
# este cadeado serializa o avanço da mesa entre todas as requisições do processo.
CADEADO_MESA = threading.Lock()


class MesaRoletaService:
    """Mesa de roleta compartilhada: todos apostam na mesma rodada e no mesmo sorteio.

    A mesa pública é a que não tem código. Uma sessão privada tem código, link de convite e
    validade de 1 hora, com rodadas, histórico e chat próprios.

    O estado anda pelo relógio (sem timers/threads de fundo): cada requisição verifica se a
    rodada atual precisa fechar, sorteia e paga. Como o sorteio é gravado na rodada, o
    resultado é o mesmo para todos os jogadores e sobrevive a recarregar a página.
    """

    def __init__(self, rodadaRepo: RodadaRoletaRepo, apostaRepo: ApostaRoletaRepo,
                 resultadoRepo: ResultadoRoletaRepo, sessaoRepo: SessaoRoletaRepo,
                 usuarioRepo: UsuarioRepo, roulette: Roulette):
        self.__rodadaRepo = rodadaRepo
        self.__apostaRepo = apostaRepo
        self.__resultadoRepo = resultadoRepo
        self.__sessaoRepo = sessaoRepo
        self.__usuarioRepo = usuarioRepo
        self.__roulette = roulette

    @classmethod
    def newService(cls):
        return cls(RodadaRoletaRepo.newRepo(), ApostaRoletaRepo.newRepo(), ResultadoRoletaRepo.newRepo(),
                   SessaoRoletaRepo.newRepo(), UsuarioRepo.newRepo(), Roulette.newRoulette())

    # ------------------------------------------------------------- sessões privadas

    def criarSessao(self, req: dict):
        idUsuario = self.__converterId(req.get("idUsuario"))
        usuario = self.__usuarioRepo.consultaPorId(idUsuario) if idUsuario is not None else None

        if usuario is None:
            raise Exception("Usuário não encontrado")

        agora = agoraBrasiliaData()
        nome = str(req.get("nome") or "").strip() or f"Mesa de {usuario.getUsuario()}"

        with CADEADO_MESA:
            self.__limparSessoesExpiradas(agora)
            sessao = self.__sessaoRepo.criar(
                nome[:60],
                usuario.getId(),
                agora,
                agora + timedelta(minutes=DURACAO_SESSAO_MINUTOS)
            )

        return {
            "sessao": self.__dictSessao(sessao),
            "mensagem": f"Sessão criada! O link vale por {DURACAO_SESSAO_MINUTOS} minutos."
        }

    def enviarMensagem(self, req: dict):
        idUsuario = self.__converterId(req.get("idUsuario"))
        usuario = self.__usuarioRepo.consultaPorId(idUsuario) if idUsuario is not None else None

        if usuario is None:
            raise Exception("Usuário não encontrado")

        sessao = self.__sessaoRepo.consultarPorCodigo(req.get("codigo"))

        if sessao is None:
            raise Exception("Sessão não encontrada")

        if sessao.isExpirada(agoraBrasiliaData()):
            raise Exception("Esta sessão já expirou")

        return {"mensagem": chatSessao.enviar(sessao.getCodigo(), usuario.getId(), usuario.getUsuario(), req.get("texto"))}

    # ------------------------------------------------------------- estado da mesa

    def estado(self, req: dict = None):
        req = req or {}
        idUsuario = self.__converterId(req.get("idUsuario"))
        codigo = req.get("codigo")

        with CADEADO_MESA:
            sessao = self.__sessao(codigo)
            agora = agoraBrasiliaData()
            expirada = sessao is not None and sessao.isExpirada(agora)
            idSessao = self.__idSessao(sessao)

            # Sessão expirada não abre rodada nova, mas a que estava em andamento ainda é sorteada e paga
            rodada = self.__rodadaDaSessao(idSessao, permitirCriar=not expirada)

            if expirada:
                return self.__estadoExpirado(sessao, idUsuario)

            apostas = self.__apostaRepo.consultarPorRodada(rodada.getId())
            fase, segundosRestantes = self.__fase(rodada, agora)
            historico = self.__rodadaRepo.consultarSorteadas(idSessao, 12)

        usuario = self.__usuarioRepo.consultaPorId(idUsuario) if idUsuario is not None else None
        estado = self.__montarEstado(rodada, apostas, fase, segundosRestantes, usuario, historico, sessao)
        estado["chat"] = chatSessao.novas(sessao.getCodigo(), req.get("desdeChat", 0)) if sessao else []
        estado["participantes"] = self.__participantes(codigo, usuario, apostas, rodada)

        if fase == "girando":
            self.__esconderResultado(estado, rodada.getId())

        return estado

    def apostar(self, req: dict):
        idUsuario = self.__converterId(req.get("idUsuario"))

        if idUsuario is None:
            raise Exception("Usuário inválido")

        apostaJogador, tipo = self.__roulette.interpretarAposta(req.get("bet"))
        valorAposta = self.__validarValor(req.get("bet_amount"))
        codigo = req.get("codigo")

        usuario = self.__usuarioRepo.consultaPorId(idUsuario)

        if usuario is None:
            raise Exception("Usuário não encontrado")

        with CADEADO_MESA:
            sessao = self.__sessao(codigo)

            if sessao is not None and sessao.isExpirada(agoraBrasiliaData()):
                raise Exception("Esta sessão já expirou. Crie uma nova mesa para continuar jogando.")

            idSessao = self.__idSessao(sessao)
            rodada = self.__rodadaDaSessao(idSessao)
            agora = agoraBrasiliaData()
            fase, segundosRestantes = self.__fase(rodada, agora)

            if fase != "apostando":
                raise Exception("A rodada já começou a girar. Aguarde a próxima rodada para apostar.")

            idRodadaCliente = req.get("idRodada")

            if idRodadaCliente is not None and str(idRodadaCliente) != str(rodada.getId()):
                raise Exception("A rodada virou. Aguarde a próxima rodada para apostar.")

            # O saldo lido antes do cadeado pode estar velho: relê já dentro da seção crítica
            usuario = self.__usuarioRepo.consultaPorId(idUsuario)

            if usuario.getSaldo() < valorAposta:
                raise Exception("Saldo insuficiente para essa aposta. Deposite mais para continuar jogando.")

            aposta = ApostaRoleta.newModel()
            aposta.setIdRodada(rodada.getId())
            aposta.setIdJogador(usuario.getId())
            aposta.setNome(usuario.getUsuario())
            aposta.setAposta(apostaJogador)
            aposta.setTipo(tipo)
            aposta.setValorAposta(valorAposta)
            aposta.setDataHora(agoraBrasilia())

            self.__debitar(usuario, valorAposta)
            self.__apostaRepo.create(aposta)

            apostas = self.__apostaRepo.consultarPorRodada(rodada.getId())
            fase, segundosRestantes = self.__fase(rodada, agoraBrasiliaData())
            historico = self.__rodadaRepo.consultarSorteadas(idSessao, 12)

        estado = self.__montarEstado(rodada, apostas, fase, segundosRestantes, usuario, historico, sessao)
        estado["mensagem"] = f"Aposta de {self.__formatar(valorAposta)} em {self.__nomeAposta(apostaJogador, tipo)} confirmada!"
        estado["participantes"] = self.__participantes(codigo, usuario, apostas, rodada)

        if fase == "girando":
            self.__esconderResultado(estado, rodada.getId())

        return estado

    # ------------------------------------------------------------- andamento da mesa

    def __sessao(self, codigo):
        """Limpa o que venceu e devolve a sessão do código informado (None = mesa pública)."""
        self.__limparSessoesExpiradas(agoraBrasiliaData())

        if not codigo:
            return None

        sessao = self.__sessaoRepo.consultarPorCodigo(codigo)

        if sessao is None:
            raise Exception("Sessão não encontrada. O link pode estar errado ou a sessão já foi encerrada.")

        return sessao

    @staticmethod
    def __idSessao(sessao):
        return sessao.getId() if sessao is not None else None

    def __rodadaDaSessao(self, idSessao, permitirCriar=True):
        """Devolve a rodada do ciclo atual, criando/sorteando o que for necessário. Exige o cadeado."""
        agora = agoraBrasiliaData()
        rodada = self.__rodadaRepo.consultarUltima(idSessao)

        if rodada is None:
            return self.__criarRodada(agora, idSessao) if permitirCriar else None

        if permitirCriar:
            rodada = self.__alinharCiclo(rodada, agora, idSessao)

        if not rodada.isSorteada() and agora >= rodada.getDataHoraFechamento():
            rodada = self.__sortearEPagar(rodada)

        return rodada

    def __criarRodada(self, inicio, idSessao=None):
        return self.__rodadaRepo.criar(inicio, inicio + timedelta(seconds=DURACAO_APOSTA), idSessao)

    def __fimCiclo(self, rodada):
        return rodada.getDataHoraFechamento() + timedelta(seconds=DURACAO_GIRO + DURACAO_RESULTADO)

    def __alinharCiclo(self, rodada, agora, idSessao):
        """Se o ciclo da rodada já terminou, cria a rodada do ciclo atual (pulando os ciclos ociosos)."""
        fimCiclo = self.__fimCiclo(rodada)

        if agora < fimCiclo:
            return rodada

        ciclosPassados = int((agora - fimCiclo).total_seconds() // DURACAO_CICLO)

        return self.__criarRodada(fimCiclo + timedelta(seconds=DURACAO_CICLO * ciclosPassados), idSessao)

    def __fase(self, rodada, agora):
        fechamento = rodada.getDataHoraFechamento()
        fimGiro = fechamento + timedelta(seconds=DURACAO_GIRO)
        fimCiclo = self.__fimCiclo(rodada)

        if agora < fechamento:
            return "apostando", self.__segundos(agora, fechamento)

        if agora < fimGiro:
            return "girando", self.__segundos(agora, fimGiro)

        return "resultado", self.__segundos(agora, fimCiclo)

    @staticmethod
    def __segundos(agora, limite):
        restante = (limite - agora).total_seconds()
        return max(0, int(restante + 0.999))

    def __sortearEPagar(self, rodada):
        if not rodada.isSorteada():
            sorteio = self.__roulette.sortear()
            rodada = self.__rodadaRepo.registrarSorteio(rodada.getId(), sorteio.get("randomNumber"), sorteio.get("result"))

        # Paga só o que ainda está pendente: se a gravação falhar no meio, a próxima passada completa
        for aposta in self.__apostaRepo.consultarNaoPagas(rodada.getId()):
            self.__pagar(aposta, rodada)

        return rodada

    def __pagar(self, aposta: ApostaRoleta, rodada):
        venceu = self.__roulette.venceu(aposta.getTipo(), aposta.getAposta(), rodada.getCor(), rodada.getNumero())
        multiplicador = self.__roulette.multiplicador(aposta.getTipo())
        valorRecebido = round(aposta.getValorAposta() * multiplicador, 2) if venceu else 0.0
        lucro = round(valorRecebido - aposta.getValorAposta(), 2)

        self.__apostaRepo.registrarPagamento(aposta.getId(), 1 if venceu else 0, valorRecebido, lucro)

        usuario = self.__usuarioRepo.consultaPorId(int(aposta.getIdJogador()))

        if venceu and usuario is not None:
            self.__creditar(usuario, valorRecebido)

        self.__registrarHistorico(aposta, rodada, venceu, valorRecebido)

    def __registrarHistorico(self, aposta: ApostaRoleta, rodada, venceu: bool, valorRecebido: float):
        """Grava em RESULTADOS_ROLETA para o histórico/estatísticas continuarem valendo para a mesa."""
        resultado = ResultadoRoleta.newModel()
        resultado.setIdJogador(aposta.getIdJogador())
        resultado.setApostaJogador(aposta.getAposta())
        resultado.setValorAposta(aposta.getValorAposta())
        resultado.setResultado(f"{rodada.getCor()} {rodada.getNumero()}")
        resultado.setValorResultado(valorRecebido if venceu else aposta.getValorAposta())
        resultado.setGanhou(1 if venceu else 0)
        resultado.setDataHora(agoraBrasilia())
        self.__resultadoRepo.create(resultado)

    # ------------------------------------------------------------- limpeza das sessões

    def __limparSessoesExpiradas(self, agora):
        """Apaga as sessões vencidas (com rodadas, apostas e chat) depois da carência."""
        limite = agora - timedelta(minutes=GRACA_EXPIRACAO_MINUTOS)

        for sessao in self.__sessaoRepo.consultarExpiradas(limite):
            idSessao = sessao.getId()

            # Rodada que ficou aberta quando a sessão venceu ainda é sorteada e paga
            for rodada in self.__rodadaRepo.consultarNaoSorteadas(idSessao, 5):
                self.__sortearEPagar(rodada)

            self.__apostaRepo.deletarPorRodadas(self.__rodadaRepo.consultarIdsPorSessao(idSessao))
            self.__rodadaRepo.deletarPorSessao(idSessao)
            self.__sessaoRepo.deletar(idSessao)
            chatSessao.limpar(sessao.getCodigo())
            presencaMesa.limpar(sessao.getCodigo())

    # ------------------------------------------------------------- saldo

    def __debitar(self, usuario, valor: float):
        usuario.setSaldo(round(usuario.getSaldo() - valor, 2))
        self.__usuarioRepo.update(usuario)

    def __creditar(self, usuario, valor: float):
        usuario.setSaldo(round(usuario.getSaldo() + valor, 2))
        self.__usuarioRepo.update(usuario)

    # ------------------------------------------------------------- montagem da resposta

    def __montarEstado(self, rodada, apostas, fase, segundosRestantes, usuario, historico, sessao):
        idUsuario = usuario.getId() if usuario is not None else None
        minhas = [a for a in apostas if str(a.getIdJogador()) == str(idUsuario)]

        return {
            "idRodada": rodada.getId(),
            "fase": fase,
            "segundosRestantes": segundosRestantes,
            "numero": rodada.getNumero(),
            "cor": rodada.getCor(),
            "sorteada": rodada.isSorteada(),
            "apostas": [a.getDict() for a in apostas],
            "jogadores": self.__agruparPorJogador(apostas),
            "minhasApostas": [a.getDict() for a in minhas],
            "meuTotal": round(sum(a.getValorAposta() for a in minhas), 2),
            "meuLucro": round(sum(a.getLucro() or 0 for a in minhas), 2) if rodada.isSorteada() and minhas else 0.0,
            "saldo": usuario.getSaldo() if usuario is not None else None,
            "totalNaMesa": round(sum(a.getValorAposta() for a in apostas), 2),
            "duracao": {
                "aposta": DURACAO_APOSTA,
                "giro": DURACAO_GIRO,
                "resultado": DURACAO_RESULTADO,
                "ciclo": DURACAO_CICLO
            },
            "apostaMinima": APOSTA_MINIMA,
            "apostaMaxima": APOSTA_MAXIMA,
            "sessao": self.__dictSessao(sessao) if sessao is not None else None,
            "historico": [
                {"idRodada": r.getId(), "numero": r.getNumero(), "cor": r.getCor()}
                for r in historico
            ]
        }

    def __estadoExpirado(self, sessao, idUsuario):
        usuario = self.__usuarioRepo.consultaPorId(idUsuario) if idUsuario is not None else None

        return {
            "idRodada": None,
            "fase": "expirada",
            "segundosRestantes": 0,
            "numero": None,
            "cor": None,
            "sorteada": False,
            "apostas": [],
            "jogadores": [],
            "minhasApostas": [],
            "meuTotal": 0.0,
            "meuLucro": 0.0,
            "saldo": usuario.getSaldo() if usuario else None,
            "totalNaMesa": 0.0,
            "duracao": {
                "aposta": DURACAO_APOSTA,
                "giro": DURACAO_GIRO,
                "resultado": DURACAO_RESULTADO,
                "ciclo": DURACAO_CICLO
            },
            "apostaMinima": APOSTA_MINIMA,
            "apostaMaxima": APOSTA_MAXIMA,
            "sessao": self.__dictSessao(sessao),
            "historico": [],
            "chat": [],
            "participantes": {"lista": [], "online": 0, "apostando": 0},
            "expirada": True,
            "mensagem": "Esta sessão expirou. Crie uma nova mesa para jogar com os amigos."
        }

    def __esconderResultado(self, estado, idRodada):
        """Durante o giro o sorteio já aconteceu no banco, mas não pode aparecer na tela antes da roda."""
        estado["numero"] = None
        estado["cor"] = None
        estado["meuLucro"] = 0.0
        estado["historico"] = [
            item for item in estado["historico"]
            if str(item["idRodada"]) != str(idRodada)
        ]

        for aposta in estado["apostas"] + estado["minhasApostas"]:
            aposta["ganhou"] = None
            aposta["valorRecebido"] = 0.0
            aposta["lucro"] = None

        for jogador in estado["jogadores"]:
            jogador["lucro"] = None
            jogador["venceu"] = False
            jogador["pago"] = False

        for pessoa in (estado.get("participantes") or {}).get("lista", []):
            pessoa["lucro"] = None
            pessoa["pago"] = False

        return estado

    @staticmethod
    def __dictSessao(sessao):
        if sessao is None:
            return None

        dados = sessao.getDict()
        dados["segundosRestantes"] = sessao.segundosRestantes(agoraBrasiliaData())
        dados["duracaoMinutos"] = DURACAO_SESSAO_MINUTOS

        return dados

    def __participantes(self, codigo, usuario, apostas, rodada):
        """Quem está com a mesa aberta agora, com o que apostou na rodada atual."""
        if usuario is not None:
            presencaMesa.marcar(codigo, usuario.getId(), usuario.getUsuario())

        grupos = {jogador["idJogador"]: jogador for jogador in self.__agruparPorJogador(apostas)}
        participantes = {}

        for presente in presencaMesa.presentes(codigo):
            participantes[presente["idJogador"]] = {
                "idJogador": presente["idJogador"],
                "nome": presente["nome"],
                "online": True
            }

        for chave, grupo in grupos.items():
            participante = participantes.setdefault(chave, {
                "idJogador": chave,
                "nome": grupo["nome"],
                "online": False
            })

            participante["total"] = grupo["total"]
            participante["quantidade"] = grupo["quantidade"]
            participante["pago"] = grupo["pago"] and rodada.isSorteada()
            participante["lucro"] = grupo["lucro"] if rodada.isSorteada() else None

        for participante in participantes.values():
            participante.setdefault("total", 0.0)
            participante.setdefault("quantidade", 0)
            participante.setdefault("lucro", None)
            participante.setdefault("pago", False)
            participante["apostou"] = participante["quantidade"] > 0

        lista = sorted(
            participantes.values(),
            key=lambda pessoa: (not pessoa["online"], -pessoa["total"], str(pessoa["nome"]).lower())
        )

        return {
            "lista": lista,
            "online": sum(1 for pessoa in lista if pessoa["online"]),
            "apostando": sum(1 for pessoa in lista if pessoa["apostou"])
        }

    @staticmethod
    def __agruparPorJogador(apostas):
        jogadores = {}

        for aposta in apostas:
            chave = str(aposta.getIdJogador())
            jogador = jogadores.setdefault(chave, {
                "idJogador": chave,
                "nome": aposta.getNome(),
                "total": 0.0,
                "quantidade": 0,
                "lucro": 0.0,
                "venceu": False,
                "pago": True
            })

            jogador["total"] = round(jogador["total"] + aposta.getValorAposta(), 2)
            jogador["quantidade"] += 1
            jogador["lucro"] = round(jogador["lucro"] + (aposta.getLucro() or 0), 2)
            jogador["venceu"] = jogador["venceu"] or aposta.getGanhou() == 1
            jogador["pago"] = jogador["pago"] and aposta.isPaga()

        return sorted(jogadores.values(), key=lambda jogador: (-jogador["total"], str(jogador["nome"]).lower()))

    # ------------------------------------------------------------- apoios

    def __validarValor(self, valorAposta):
        try:
            valor = round(float(valorAposta), 2)
        except (TypeError, ValueError):
            raise Exception("Valor da aposta precisa ser um número")

        if valor < APOSTA_MINIMA:
            raise Exception(f"Aposta mínima é {self.__formatar(APOSTA_MINIMA)}")

        if valor > APOSTA_MAXIMA:
            raise Exception(f"Aposta máxima é {self.__formatar(APOSTA_MAXIMA)}")

        return valor

    @staticmethod
    def __converterId(idUsuario):
        if idUsuario is None:
            return None

        try:
            return int(idUsuario)
        except (TypeError, ValueError):
            raise Exception("Usuário inválido")

    @staticmethod
    def __nomeAposta(apostaJogador, tipo):
        return f"número {apostaJogador}" if tipo == "number" else f"cor {apostaJogador}"

    @staticmethod
    def __formatar(valor):
        return f"R$ {valor:,.2f}".replace(",", "TEMP").replace(".", ",").replace("TEMP", ".")
