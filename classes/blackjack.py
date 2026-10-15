from classes.baralhoFromDb import BaralhoDb
from classes.jogador import Jogador
from classes.maoBlackjack import MaoBlackjack
from server.blackjack.models.acaoBlackjackModel import AcaoBlackjack
from server.blackjack.models.blackjackModel import BlackjackModel
from server.blackjack.models.resultadoBlackjackModel import ResultadoBlackjack
from server.blackjack.repository.acaoBlackjackRepo import AcaoBlackjackRepo
from server.blackjack.repository.blackjackRepo import BlackjackRepo
from server.blackjack.repository.cartaJogadorBlackjackRepo import CartaJogadorBlackjackRepo
from server.blackjack.repository.maoBlackjackRepo import MaoBlackjackRepo
from server.blackjack.repository.resultadoBlackjackRepo import ResultadoBlackjackRepo
from server.usuario.model.usuario import Usuario
from server.usuario.repository.usuarioRepo import UsuarioRepo
from utils import agoraBrasilia
from PIL import Image
import uuid

class Blackjack:
    APOSTA_MINIMA = 1.0
    APOSTA_MAXIMA = 1000.0

    # Multiplicador pago sobre a aposta, por motivo do resultado
    PAGAMENTOS = {
        "blackjack_jogador": 2.5,
        "blackjack_dealer": 0.0,
        "estouro_jogador": 0.0,
        "menor_valor": 0.0,
        "maior_valor": 2.0,
        "estouro_dealer": 2.0,
        "empate": 1.0,
        "ambos_blackjack": 1.0
    }

    MENSAGENS_RESULTADO = {
        "ambos_blackjack": "⚖️ Ambos têm **blackjack**. Resultado: **Empate!**",
        "blackjack_jogador": "🏆 Jogador tem **blackjack**! **Jogador ganhou!**",
        "blackjack_dealer": "❌ Dealer tem **blackjack**! **Dealer ganhou!**",
        "estouro_jogador": "💥 Jogador **estourou**! **Dealer ganhou!**",
        "estouro_dealer": "💥 Dealer **estourou**! **Jogador ganhou!**",
        "empate": "⚖️ **Empate!**",
        "menor_valor": "❌ **Dealer ganhou!**",
        "maior_valor": "🏆 **Jogador ganhou!**"
    }

    RESUMOS_RESULTADO = {
        "ambos_blackjack": {"situacao": "empate", "titulo": "Empate", "descricao": "Você e o dealer fizeram blackjack."},
        "blackjack_jogador": {"situacao": "vitoria", "titulo": "Blackjack!", "descricao": "Sua mão fechou 21 com apenas duas cartas."},
        "blackjack_dealer": {"situacao": "derrota", "titulo": "Dealer ganhou", "descricao": "O dealer fechou blackjack com duas cartas."},
        "estouro_jogador": {"situacao": "derrota", "titulo": "Você estourou", "descricao": "Sua mão passou de 21."},
        "estouro_dealer": {"situacao": "vitoria", "titulo": "Você ganhou!", "descricao": "O dealer estourou com mais de 21."},
        "empate": {"situacao": "empate", "titulo": "Empate", "descricao": "Sua mão e a do dealer terminaram com o mesmo valor."},
        "menor_valor": {"situacao": "derrota", "titulo": "Dealer ganhou", "descricao": "A mão do dealer ficou mais próxima de 21."},
        "maior_valor": {"situacao": "vitoria", "titulo": "Você ganhou!", "descricao": "Sua mão ficou mais próxima de 21 que a do dealer."}
    }

    def __init__(self, jogadorHost: Jogador = None, qtdeBaralhos: int = 4):
        self.__idJogo = None
        self.__baralho = BaralhoDb.newBaralhoFromDb(qtdeBaralhos)
        self.__jogadorHost: Jogador = jogadorHost
        self.__maos: list[MaoBlackjack] = []
        self.__idMaoAtual = None
        self.__dealer: Jogador = None
        self.__blackjackRepo = BlackjackRepo.newBlackjackRepo()
        self.__cartaJogadorRepo = CartaJogadorBlackjackRepo.newRepo()
        self.__maoRepo = MaoBlackjackRepo.newRepo()
        self.__resultados = []
        self.__financeiro = None
        self.__finalizado = False
        self.__mensagemFinal = None

    # ------------------------------------------------------------------ inicio

    @classmethod
    def iniciarJogo(cls, idJogadorHost, valorAposta: float = 0):
        return cls.__iniciarJogoInterno(idJogadorHost, valorAposta).__mensagemRetorno()

    @classmethod
    def iniciarJogoDict(cls, idJogadorHost, valorAposta: float = 0):
        blackjack = cls.__iniciarJogoInterno(idJogadorHost, valorAposta)
        return blackjack.getEstadoJogo(mensagem=blackjack.__mensagemRetorno())

    @classmethod
    def __iniciarJogoInterno(cls, idJogadorHost, valorAposta: float = 0):
        blackjack = cls()
        usuarioRepo = UsuarioRepo.newRepo()

        if blackjack.__blackjackRepo.consultarJogoIdJogador(idJogadorHost):
            raise Exception("O jogador já está em um jogo de blackjack")

        jogadorHost = usuarioRepo.consultaPorId(idJogadorHost)

        if jogadorHost is None:
            raise Exception("Jogador não encontrado")

        aposta = blackjack.__validarAposta(valorAposta, jogadorHost)
        blackjack.__debitarSaldo(jogadorHost, aposta)

        blackjack.__jogadorHost = Jogador.newJogador(jogadorHost.getId(), jogadorHost.getUsuario())
        dealer = blackjack.__obterDealer(usuarioRepo)
        blackjack.__dealer = Jogador.newJogador(dealer.getId(), "dealer")

        jogoCriado = blackjack.__blackjackRepo.createNovoJogo(
            BlackjackModel.newBlackjackModel(dict(
                idJogadorHost=blackjack.__jogadorHost.getId(),
                valorAposta=aposta
            ))
        )
        blackjack.__idJogo = jogoCriado.getId()

        primeiraMao = blackjack.__novaMao(0, aposta)
        blackjack.__maos.append(primeiraMao)
        blackjack.__idMaoAtual = primeiraMao.getIndice()
        blackjack.__maoRepo.create(blackjack.__idJogo, primeiraMao)

        blackjack.__darCarta(primeiraMao, "inicio")
        blackjack.__darCarta(primeiraMao, "inicio")
        blackjack.__darCartaDealer("inicio")

        return blackjack

    # ------------------------------------------------------------------ retomar

    @classmethod
    def restateJogo(cls, idJogador, nomeJogador=None):
        blackjack = cls.__carregarJogoInterno(idJogador, nomeJogador)
        return blackjack.__mensagemFinal if blackjack.__finalizado else blackjack.__mensagemRetorno()

    @classmethod
    def restateJogoDict(cls, idJogador, nomeJogador=None):
        blackjack = cls.__carregarJogoInterno(idJogador, nomeJogador)

        if blackjack.__finalizado:
            return blackjack.getEstadoJogo(mensagem=blackjack.__mensagemFinal, finalizado=True)

        return blackjack.getEstadoJogo(mensagem=blackjack.__mensagemRetorno())

    @classmethod
    def __carregarJogoInterno(cls, idJogador, nomeJogador=None):
        blackjack = cls()
        usuario = UsuarioRepo.newRepo().consultaPorId(idJogador)

        if nomeJogador is None and usuario is not None:
            nomeJogador = usuario.getUsuario()

        blackjack.__jogadorHost = Jogador.newJogador(idJogador, nomeJogador)
        jogo = blackjack.__blackjackRepo.consultarJogoIdJogador(idJogador)

        if jogo is None:
            raise Exception("Jogador ainda não está em nenhum jogo")

        blackjack.__idJogo = jogo.getId()

        maos = blackjack.__maoRepo.consultarPorJogo(jogo.getId())

        if not maos:
            maos = [blackjack.__novaMao(0, float(jogo.getValorAposta() or 0))]

        for mao in maos:
            mao.getJogador().setId(idJogador)

            for registro in blackjack.__cartaJogadorRepo.consultarCartasMao(jogo.getId(), idJogador, mao.getIndice()):
                carta = blackjack.__baralho.deal(registro.getIdCarta())

                if carta:
                    mao.addCard(carta)

            blackjack.__maos.append(mao)

            if not mao.isEncerrada() and blackjack.__idMaoAtual is None:
                blackjack.__idMaoAtual = mao.getIndice()

        dealer = blackjack.__obterDealer(UsuarioRepo.newRepo())
        blackjack.__dealer = Jogador.newJogador(dealer.getId(), "dealer")

        for registro in blackjack.__cartaJogadorRepo.consultarCartasMao(jogo.getId(), blackjack.__dealer.getId(), -1):
            carta = blackjack.__baralho.deal(registro.getIdCarta())

            if carta:
                blackjack.__dealer.addCard(carta)

        # Rodada interrompida entre fechar a última mão e o pagamento: finaliza agora
        if blackjack.__idMaoAtual is None:
            blackjack.__jogadaDealer()
            blackjack.__mensagemFinal = blackjack.__avaliarVencedor()
            blackjack.__finalizado = True

        return blackjack

    # ------------------------------------------------------------------ jogadas

    @classmethod
    def jogadaJogador(cls, idJogador, nomeJogador=None, jogada: int = None):
        blackjack, mensagem, finalizado = cls.__executarJogada(idJogador, nomeJogador, jogada)
        return mensagem

    @classmethod
    def jogadaJogadorDict(cls, idJogador, jogada: int, nomeJogador=None):
        blackjack, mensagem, finalizado = cls.__executarJogada(idJogador, nomeJogador, jogada)
        return blackjack.getEstadoJogo(mensagem=mensagem, finalizado=finalizado)

    @classmethod
    def __executarJogada(cls, idJogador, nomeJogador, jogada: int):
        blackjack = cls.__carregarJogoInterno(idJogador, nomeJogador)

        if blackjack.__finalizado:
            return blackjack, blackjack.__mensagemFinal, True

        mao = blackjack.__maoAtual()

        if jogada == 0:
            blackjack.__registrarAcao("parar", "jogador", None, mao.getIndice())
            return blackjack.__encerrarMao()

        if jogada == 1:
            if mao.getValorMao() >= 21:
                raise Exception("Jogador não pode comprar")

            blackjack.__darCarta(mao, "comprar")

            if mao.getValorMao() > 21:
                return blackjack.__encerrarMao()

            return blackjack, blackjack.__mensagemRetorno(), False

        if jogada == 2:
            if len(mao.getCartas()) > 2:
                raise Exception("Jogador não pode dobrar")

            blackjack.__dobrarAposta(mao)
            blackjack.__darCarta(mao, "dobrar")
            return blackjack.__encerrarMao()

        if jogada == 3:
            blackjack.__dividirMao(mao)
            return blackjack, blackjack.__mensagemRetorno(), False

        raise Exception(f"Jogada {jogada} inválida")

    def __encerrarMao(self):
        mao = self.__maoAtual()
        mao.encerrar()
        self.__maoRepo.atualizar(self.__idJogo, mao)

        proxima = self.__proximaMao()

        if proxima is not None:
            self.__idMaoAtual = proxima.getIndice()
            return self, self.__mensagemRetorno(), False

        self.__jogadaDealer()
        return self, self.__avaliarVencedor(), True

    def __dividirMao(self, mao: MaoBlackjack):
        if not self.verificarJogadorPodeDividir(mao):
            raise Exception("Jogador não pode dividir")

        usuario = UsuarioRepo.newRepo().consultaPorId(self.__jogadorHost.getId())

        if usuario.getSaldo() < mao.getValorAposta():
            raise Exception("Usuário não tem saldo suficiente para dividir!")

        self.__debitarSaldo(usuario, mao.getValorAposta())

        indice = self.__proximoIndiceMao()
        novaMao = self.__novaMao(indice, mao.getValorAposta())
        novaMao.addCard(mao.removerUltimaCarta())

        # A ordem das mãos é sempre a ordem de criação (índice crescente): assim a lista
        # continua igual depois de recarregar do banco e a mão atual nunca "pula".
        self.__maos.append(novaMao)
        self.__maoRepo.create(self.__idJogo, novaMao)

        self.__registrarAcao("dividir", "jogador", None, mao.getIndice())
        self.__darCarta(mao, "inicio")
        self.__darCarta(novaMao, "inicio")

        self.__regravarCartas(mao)
        self.__regravarCartas(novaMao)

    def __jogadaDealer(self):
        while self.verificarDealerPodeContinuar():
            self.__darCartaDealer("dealer")

    # ------------------------------------------------------------------ avaliacao

    def verificarDealerPodeContinuar(self):
        if self.__dealer.getValorMao() == 21:
            return False

        if self.__dealer.getValorMao() > 21:
            return False

        if self.__dealer.getValorMao() >= 17:
            return False

        return True

    def verificarJogadorPodeDividir(self, mao: MaoBlackjack):
        cartas = mao.getCartas()

        if len(cartas) != 2:
            return False

        return cartas[0].getValor() == cartas[1].getValor()

    def __definirMotivo(self, mao: MaoBlackjack, valorJogador: int, valorDealer: int):
        blackjackJogador = len(mao.getCartas()) == 2 and valorJogador == 21
        blackjackDealer = len(self.__dealer.getCards()) == 2 and valorDealer == 21

        if blackjackJogador and blackjackDealer:
            return "ambos_blackjack"

        if blackjackJogador:
            return "blackjack_jogador"

        if blackjackDealer:
            return "blackjack_dealer"

        if valorJogador > 21:
            return "estouro_jogador"

        if valorDealer > 21:
            return "estouro_dealer"

        if valorJogador == valorDealer:
            return "empate"

        return "menor_valor" if valorJogador < valorDealer else "maior_valor"

    def __avaliarJogador(self, mao: MaoBlackjack):
        valorJogador = mao.getValorMao()
        valorDealer = self.__dealer.getValorMao()
        motivo = self.__definirMotivo(mao, valorJogador, valorDealer)
        resumo = self.RESUMOS_RESULTADO[motivo]

        return {
            "indiceMao": mao.getIndice(),
            "nomeMao": mao.getNome(),
            "aposta": mao.getValorAposta(),
            "jogador": mao.getNome(),
            "valorJogador": valorJogador,
            "cartasJogador": ", ".join([f"{c.getRank()} de {c.getSuit()}" for c in mao.getCartas()]),
            "valorDealer": valorDealer,
            "cartasDealer": ", ".join([f"{c.getRank()} de {c.getSuit()}" for c in self.__dealer.getCards()]),
            "motivo": motivo,
            "situacao": resumo["situacao"],
            "titulo": resumo["titulo"],
            "descricao": resumo["descricao"]
        }

    def __avaliarVencedor(self):
        """Avalia todas as mãos, paga cada aposta e guarda o histórico."""
        self.__resultados = [self.__avaliarJogador(mao) for mao in self.__maos]

        self.__liquidarAposta()

        for resultado in self.__resultados:
            self.__registrarResultado(resultado)

        self.__finalizarJogo()

        return "\n-----------------------------------------\n".join(
            self.MENSAGENS_RESULTADO[resultado["motivo"]] for resultado in self.__resultados
        )

    def verificarVencedor(self):
        return self.__avaliarVencedor()

    # ------------------------------------------------------------------ estado

    def __maoAtual(self) -> MaoBlackjack:
        for mao in self.__maos:
            if mao.getIndice() == self.__idMaoAtual:
                return mao

        return None

    def __proximaMao(self) -> MaoBlackjack:
        for indice, mao in enumerate(self.__maos):
            if mao.getIndice() == self.__idMaoAtual and indice + 1 < len(self.__maos):
                return self.__maos[indice + 1]

        return None

    def __proximoIndiceMao(self) -> int:
        return max(mao.getIndice() for mao in self.__maos) + 1

    def __nomeMao(self, indice: int) -> str:
        if indice == 0:
            return self.__jogadorHost.getNomeJogador()

        return f"{self.__jogadorHost.getNomeJogador()} - Mão {indice + 1}"

    def __saldoDisponivel(self):
        usuario = UsuarioRepo.newRepo().consultaPorId(self.__jogadorHost.getId())
        return usuario.getSaldo() if usuario else 0

    def __totalApostado(self):
        return round(sum(mao.getValorAposta() for mao in self.__maos), 2)

    def getAcoesDisponiveis(self, mao: MaoBlackjack = None):
        """
        Jogadas que a mão atual aceita. A divisão aparece sempre que a mão tem duas
        cartas de mesmo valor (inclusive A-A), permitindo dividir de novo se vier par.
        """
        mao = mao or self.__maoAtual()
        acoes = []

        if mao is None:
            return acoes

        saldo = self.__saldoDisponivel()
        aposta = mao.getValorAposta()

        acoes.append({"codigo": 0, "nome": "parar", "descricao": "Parar"})

        if mao.getValorMao() < 21:
            acoes.append({"codigo": 1, "nome": "comprar", "descricao": "Comprar carta"})

            if len(mao.getCartas()) <= 2:
                acoes.append(self.__acaoComSaldo(
                    2, "dobrar", "Dobrar", saldo >= aposta,
                    f"Dobrar exige mais R$ {aposta:.2f} de saldo"
                ))

        if self.verificarJogadorPodeDividir(mao):
            acoes.append(self.__acaoComSaldo(
                3, "dividir", "Dividir", saldo >= aposta,
                f"Dividir exige mais R$ {aposta:.2f} de saldo"
            ))

        return acoes

    @staticmethod
    def __acaoComSaldo(codigo: int, nome: str, descricao: str, habilitada: bool, motivo: str):
        """Marca a ação como indisponível (com o motivo) em vez de simplesmente escondê-la."""
        return {
            "codigo": codigo,
            "nome": nome,
            "descricao": descricao,
            "habilitada": habilitada,
            "motivoIndisponivel": None if habilitada else f"Saldo insuficiente. {motivo}."
        }

    def verificarJogadasJogador(self, mao: MaoBlackjack = None):
        return ", ".join(f"{acao['codigo']}: {acao['nome']}" for acao in self.getAcoesDisponiveis(mao))

    def getIdJogo(self):
        return self.__idJogo

    def getDict(self):
        maoAtual = self.__maoAtual()

        return {
            "idJogo": self.__idJogo,
            "jogadorHost": {
                "id": self.__jogadorHost.getId(),
                "nome": self.__jogadorHost.getNomeJogador(),
                "valorMao": maoAtual.getValorMao() if maoAtual else 0,
                "cartas": [c.getDict() for c in maoAtual.getCartas()] if maoAtual else []
            } if self.__jogadorHost else None,
            "idMaoAtual": self.__idMaoAtual,
            "aposta": self.__totalApostado(),
            "maos": [mao.getDict() for mao in self.__maos],
            "dealer": {
                "id": self.__dealer.getId(),
                "nome": self.__dealer.getNomeJogador(),
                "valorMao": self.__dealer.getValorMao(),
                "valoresParciais": self.__dealer.getValoresParciais(),
                "cartas": [c.getDict() for c in self.__dealer.getCards()]
            } if self.__dealer else None,
            "jogadores": [mao.getDict() for mao in self.__maos]
        }

    def getEstadoJogo(self, mensagem: str = None, finalizado: bool = False):
        """
        Estado estruturado da rodada (mãos, cartas, valores e jogadas disponíveis) para o front.
        """
        estado = self.getDict()
        estado["ativo"] = True
        estado["finalizado"] = finalizado or self.__finalizado
        estado["mensagem"] = mensagem
        estado["resultado"] = mensagem if estado["finalizado"] else None
        estado["aposta"] = self.__totalApostado()
        estado["resultados"] = self.__resultados
        estado["financeiro"] = self.__financeiro
        estado["acoes"] = [] if estado["finalizado"] else self.getAcoesDisponiveis()
        return estado

    # ------------------------------------------------------------------ saldo

    def __validarAposta(self, valorAposta, usuario):
        try:
            aposta = round(float(valorAposta), 2)
        except (TypeError, ValueError):
            raise Exception("Valor da aposta precisa ser um número")

        if aposta < self.APOSTA_MINIMA:
            raise Exception(f"Aposta mínima é {self.APOSTA_MINIMA:.2f}")

        if aposta > self.APOSTA_MAXIMA:
            raise Exception(f"Aposta máxima é {self.APOSTA_MAXIMA:.2f}")

        if usuario.getSaldo() < aposta:
            raise Exception("Usuário não tem saldo suficiente para realizar essa aposta!")

        return aposta

    def __debitarSaldo(self, usuario, valor):
        usuario.setSaldo(round(usuario.getSaldo() - valor, 2))
        UsuarioRepo.newRepo().update(usuario)

    def __dobrarAposta(self, mao: MaoBlackjack):
        usuario = UsuarioRepo.newRepo().consultaPorId(self.__jogadorHost.getId())

        if usuario.getSaldo() < mao.getValorAposta():
            raise Exception("Usuário não tem saldo suficiente para dobrar a aposta!")

        self.__debitarSaldo(usuario, mao.getValorAposta())
        mao.setValorAposta(round(mao.getValorAposta() * 2, 2))
        self.__maoRepo.atualizar(self.__idJogo, mao)

    def __liquidarAposta(self):
        """
        As apostas foram debitadas ao iniciar (e a cada divisão/dobra); aqui devolvemos
        o valor pago conforme o resultado de cada mão, no mesmo padrão do RouletteService.
        """
        totalApostado = self.__totalApostado()

        if totalApostado <= 0:
            return

        totalRecebido = 0

        for resultado in self.__resultados:
            aposta = resultado["aposta"]
            multiplicador = self.PAGAMENTOS.get(resultado["motivo"], 0)
            recebido = round(aposta * multiplicador, 2)

            resultado["valorRecebido"] = recebido
            resultado["lucro"] = round(recebido - aposta, 2)
            totalRecebido += recebido

        usuario = UsuarioRepo.newRepo().consultaPorId(self.__jogadorHost.getId())
        usuario.setSaldo(round(usuario.getSaldo() + totalRecebido, 2))
        UsuarioRepo.newRepo().update(usuario)

        self.__financeiro = {
            "aposta": totalApostado,
            "valorRecebido": round(totalRecebido, 2),
            "lucro": round(totalRecebido - totalApostado, 2),
            "saldo": usuario.getSaldo()
        }

    # ------------------------------------------------------------------ apoio

    @staticmethod
    def __obterDealer(usuarioRepo: UsuarioRepo):
        """Busca o usuário dealer e o cria caso a base tenha sido limpa."""
        dealer = usuarioRepo.consultarPorUsuario("dealer")

        if dealer is None:
            dealer = usuarioRepo.criarDealer()

        return dealer

    def __novaMao(self, indice: int, valorAposta: float) -> MaoBlackjack:
        mao = MaoBlackjack.newMao(dict(indice=indice, valor_aposta=valorAposta, nome=self.__nomeMao(indice)))
        mao.getJogador().setId(self.__jogadorHost.getId())
        return mao

    def __darCarta(self, mao: MaoBlackjack, acao: str):
        carta = self.__baralho.deal()

        if carta is None:
            raise Exception("Não há mais cartas no baralho")

        mao.addCard(carta)
        self.__cartaJogadorRepo.createCarta(self.__idJogo, self.__jogadorHost.getId(), carta.getId(), mao.getIndice())
        self.__registrarAcao(acao, "jogador", carta, mao.getIndice())

        return carta

    def __darCartaDealer(self, acao: str):
        carta = self.__baralho.deal()

        if carta is None:
            raise Exception("Não há mais cartas no baralho")

        self.__dealer.addCard(carta)
        self.__cartaJogadorRepo.createCarta(self.__idJogo, self.__dealer.getId(), carta.getId(), -1)
        self.__registrarAcao(acao, "dealer", carta, -1)

        return carta

    def __regravarCartas(self, mao: MaoBlackjack):
        self.__cartaJogadorRepo.deletarCartasMao(self.__idJogo, self.__jogadorHost.getId(), mao.getIndice())

        for carta in mao.getCartas():
            self.__cartaJogadorRepo.createCarta(self.__idJogo, self.__jogadorHost.getId(), carta.getId(), mao.getIndice())

    def __registrarAcao(self, acao: str, dono: str, carta=None, indiceMao: int = 0):
        """Guarda cada passo da mão (início, ações do jogador e cartas do dealer) para o replay."""
        if self.__idJogo is None:
            return

        registro = AcaoBlackjack.newModel()
        registro.setIdJogo(self.__idJogo)
        registro.setIdJogador(self.__jogadorHost.getId() if self.__jogadorHost else None)
        registro.setIndiceMao(indiceMao)
        registro.setAcao(acao)
        registro.setDono(dono)
        registro.setCarta(carta.getNomeImagem() if carta else None)
        registro.setValorJogador(self.__valorMaoPorIndice(indiceMao) if dono != "dealer" else self.__valorTotalJogador())
        registro.setValorDealer(self.__dealer.getValorMao() if self.__dealer else 0)
        registro.setDataHora(agoraBrasilia())

        AcaoBlackjackRepo.newRepo().create(registro)

    def __valorMaoPorIndice(self, indiceMao: int) -> int:
        for mao in self.__maos:
            if mao.getIndice() == indiceMao:
                return mao.getValorMao()

        return 0

    def __valorTotalJogador(self) -> int:
        return sum(mao.getValorMao() for mao in self.__maos)

    def __mensagemRetorno(self):
        detalhes = []

        for mao in self.__maos:
            cartas = ", ".join(f"{c.getRank()} de {c.getSuit()}" for c in mao.getCartas())
            detalhes.append(
                f"👤 **{mao.getNome()}**\n"
                f"Cartas: {cartas}\n"
                f"Valor da mão: **{mao.getValorMao()}**"
            )

        cartasDealer = ", ".join(f"{c.getRank()} de {c.getSuit()}" for c in self.__dealer.getCards())
        jogadas = self.verificarJogadasJogador()

        return (
            f"🎴 **Status da Rodada** 🎴\n\n"
            + "\n\n".join(detalhes) +
            f"\n\n🤵 **Dealer**\n"
            f"Cartas: {cartasDealer}\n"
            f"Valor da mão: **{self.__dealer.getValorMao()}**\n\n"
            f"✨ **Jogadas possíveis**: {jogadas if jogadas else 'Nenhuma'}"
        )

    def __finalizarJogo(self):
        self.__cartaJogadorRepo.deletarTodasCartasJogo(self.__idJogo)
        self.__maoRepo.deletarPorJogo(self.__idJogo)
        self.__blackjackRepo.deleteJogo(self.__idJogo)

    def __registrarResultado(self, resultado: dict):
        """Guarda a mão no histórico para as estatísticas do blackjack."""
        historico = ResultadoBlackjack.newModel()
        historico.setIdJogo(self.__idJogo)
        historico.setIdJogador(self.__jogadorHost.getId())
        historico.setIndiceMao(resultado["indiceMao"])
        historico.setValorAposta(resultado["aposta"])
        historico.setResultado(resultado["motivo"])
        historico.setValorJogador(resultado["valorJogador"])
        historico.setValorDealer(resultado["valorDealer"])
        historico.setValorRecebido(resultado.get("valorRecebido", 0))
        historico.setLucro(resultado.get("lucro", 0))
        historico.setDataHora(agoraBrasilia())

        ResultadoBlackjackRepo.newRepo().create(historico)

    @staticmethod
    def __gerarImagemCartas(cartas, caminhoSaida="mesaBlackjack.png"):
        """
        Gera uma imagem final juntando todas as imagens das cartas recebidas.
        Usa o método carta.getCaminhoImagem() para buscar os arquivos.
        """
        imagens = [Image.open(carta.getCaminhoImagem()) for carta in cartas]

        larguraCarta, alturaCarta = imagens[0].size
        espacamento = 25

        larguraFinal = len(imagens) * larguraCarta + (len(imagens) - 1) * espacamento
        alturaFinal = alturaCarta

        mesa = Image.new("RGB", (larguraFinal, alturaFinal), (8, 100, 48))

        x = 0
        for img in imagens:
            mesa.paste(img, (x, 0))
            x += larguraCarta + espacamento

        mesa.save(caminhoSaida)
        return caminhoSaida
