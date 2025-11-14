from classes.baralhoFromDb import BaralhoDb
from classes.jogador import Jogador
from server.blackjack.models.blackjackModel import BlackjackModel
from server.blackjack.repository.blackjackRepo import BlackjackRepo
from server.blackjack.repository.cartaJogadorBlackjackRepo import CartaJogadorBlackjackRepo
from server.usuario.repository.usuarioRepo import UsuarioRepo
from PIL import Image

class Blackjack:
    def __init__(self, jogadorHost: Jogador = None, qtdeBaralhos: int = 4):
        self.__idJogo = None
        self.__baralho = BaralhoDb.newBaralhoFromDb(qtdeBaralhos)
        self.__jogadorHost = jogadorHost
        self.__jogadores: list[Jogador] = []
        self.__dealer: Jogador = None
        self.__blackjackRepo = BlackjackRepo.newBlackjackRepo()
        self.__cartaJogadorRepo = CartaJogadorBlackjackRepo.newRepo()
        self.__jogadasJogador = []
    
    @classmethod
    def iniciarJogo(cls, idJogadorHost, nomeJogadorHost):
        blackjack = cls()
        jogo = blackjack.__blackjackRepo.consultarJogoIdJogador(idJogadorHost)
        
        if jogo:
            raise Exception("O jogador já está em um jogo de blackjack")
        
        blackjack.__jogadorHost = Jogador.newJogador(idJogadorHost, nomeJogadorHost)
        dealer = UsuarioRepo.newRepo().consultarPorUsuario("dealer")
        blackjack.__dealer = Jogador.newJogador(dealer.getId(), "dealer")
        
        carta1Jogador = blackjack.__baralho.deal()
        carta2Jogador = blackjack.__baralho.deal()
        cartaDealer = blackjack.__baralho.deal()
        
        blackjack.__jogadorHost.addCard(carta1Jogador)
        blackjack.__jogadorHost.addCard(carta2Jogador)
        blackjack.__dealer.addCard(cartaDealer)
        blackjack.__jogadores.append(blackjack.__jogadorHost)
        
        jogoCriado = blackjack.__blackjackRepo.createNovoJogo(
            BlackjackModel.newBlackjackModel(dict(idJogadorHost=blackjack.__jogadorHost.getId()))
        )
        blackjack.__idJogo = jogoCriado.getId()
        
        blackjack.__cartaJogadorRepo.createCarta(blackjack.__idJogo, blackjack.__jogadorHost.getId(), carta1Jogador.getId())
        blackjack.__cartaJogadorRepo.createCarta(blackjack.__idJogo, blackjack.__jogadorHost.getId(), carta2Jogador.getId())
        blackjack.__cartaJogadorRepo.createCarta(blackjack.__idJogo, blackjack.__dealer.getId(), cartaDealer.getId())
        
        return blackjack.__mensagemRetorno()
    
    @classmethod
    def restateJogo(cls, idJogador, nomeJogador):
        blackjack = cls()
        blackjack.__jogadorHost = Jogador.newJogador(idJogador, nomeJogador)
        jogo = blackjack.__blackjackRepo.consultarJogoIdJogador(idJogador)
        
        if jogo is None:
            raise Exception("Jogador ainda não está em nenhum jogo")
        
        blackjack.__idJogo = jogo.getId()
        dealer = UsuarioRepo.newRepo().consultarPorUsuario("dealer")
        blackjack.__dealer = Jogador.newJogador(dealer.getId(), "dealer")
        
        cartasJogoJogador = blackjack.__cartaJogadorRepo.consultarCartasJogador(jogo.getId(), jogo.getIdJogador())
        cartasDealer = blackjack.__cartaJogadorRepo.consultarCartasJogador(jogo.getId(), blackjack.__dealer.getId())
        
        for carta in cartasJogoJogador:
            blackjack.__jogadorHost.addCard(blackjack.__baralho.deal(carta.getIdCarta()))
            
        for carta in cartasDealer:
            blackjack.__dealer.addCard(blackjack.__baralho.deal(carta.getIdCarta()))
        
        return blackjack.__mensagemRetorno()
    
    @classmethod
    def jogadaJogador(cls, idJogador, nomeJogador, jogada: int):
        blackjack = cls()
        blackjack.__restateJogo(idJogador, nomeJogador)
        
        if jogada == 0:
            blackjack.__jogadaDealer()
            return blackjack.verificarVencedor()

        if jogada == 1:
            if blackjack.__jogadorHost.getValorMao() >= 21:
                raise Exception("Jogador não pode comprar")
            
            cartaAdicionar = blackjack.__baralho.deal()
            blackjack.__jogadorHost.addCard(cartaAdicionar)
            blackjack.__cartaJogadorRepo.createCarta(blackjack.__idJogo, blackjack.__jogadorHost.getId(), cartaAdicionar.getId())
            
            if blackjack.__jogadorHost.getValorMao() > 21:
                blackjack.__jogadaDealer()
                return blackjack.verificarVencedor()
            
            return blackjack.__mensagemRetorno()
                    
        if jogada == 2:
            if len(blackjack.__jogadorHost.getCards()) > 2:
                raise Exception("Jogador não pode dobrar")
                
            cartaAdicionar = blackjack.__baralho.deal()
            blackjack.__jogadorHost.addCard(cartaAdicionar)
            blackjack.__cartaJogadorRepo.createCarta(blackjack.__idJogo, blackjack.__jogadorHost.getId(), cartaAdicionar.getId())
            blackjack.__jogadaDealer()
            return blackjack.verificarVencedor()
                    
        if jogada == 3:
            raise Exception("Ainda não implementado")
    
    def getIdJogo(self):
        return self.__idJogo

    def addJogador(self, jogador: Jogador):
        for joga in self.__jogadores:
            if joga.getId() == jogador.getId():
                raise Exception(f"Jogador {jogador.getNomeJogador()} já está no jogo")
            
        self.__jogadores.append(jogador)

    def adicionarCartaJogador(self, jogador: Jogador):
        jogador.addCard(self.__baralho.deal())
        
    def adicionarCartaDealaer(self):
        self.__dealer.addCard(self.__baralho.deal())

    def verificarJogadorPodeContinuar(self, jogador: Jogador):
        if jogador.getValorMao() == 21:
            return False

        if jogador.getValorMao() > 21:
            return False

        return True
    
    def verificarJogadasJogador(self, jogador: Jogador):
        comprar = True
        dobrar = True
        dividir = True

        if len(jogador.getCards()) > 2:
            dobrar = False
            dividir = False

        if jogador.getValorMao() >= 21:
            comprar = False
            dobrar = False
            dividir = False

        opcoes = []
        
        opcoes.append("0: parar")
        if comprar:
            self.__jogadasJogador.append(1)
            opcoes.append("1: comprar")
        if dobrar:
            self.__jogadasJogador.append(2)
            opcoes.append(" 2: dobrar")
        if dividir:
            self.__jogadasJogador.append(3)
            opcoes.append(" 3: dividir")

        return ",".join(opcoes)
        
    def verificarJogadorPodeDividir(self, jogador: Jogador):
        if jogador.getCards()[0].getValor() == jogador.getCards()[1].getValor() and len(jogador.getCards()) == 2:
            return True
        
        return False
    
    def dividirMaoJogador(self, jogador: Jogador):
        carta1 = jogador.getCards()[0]
        carta2 = jogador.getCards()[1]
        
        mao1 = Jogador.newJogador()
        mao1.setNomeJogador(f"{jogador.getNomeJogador()} - Mão 1")
        mao1.setValorAposta(jogador.getValorAposta())
        mao1.addCard(carta1)
        mao1.addCard(self.__baralho.deal())
        
        mao2 = Jogador.newJogador()
        mao2.setNomeJogador(f"{jogador.getNomeJogador()} - Mão 2")
        mao2.setValorAposta(jogador.getValorAposta())
        mao2.addCard(carta2)
        mao2.addCard(self.__baralho.deal())
        
        self.jogadores = [mao1, mao2]
        
        return [mao1, mao2]
        
    def verificarDealerPodeContinuar(self):
        if self.__dealer.getValorMao() == 21:
            return False

        if self.__dealer.getValorMao() > 21:
            return False

        if self.__dealer.getValorMao() >= 17:
            return False

        return True

    def verificarVencedor(self):
        valorDealer = self.__dealer.getValorMao()
        cartasDealer = ", ".join([f"{c.getRank()} de {c.getSuit()}" for c in self.__dealer.getCards()])

        mensagens = []

        for jogador in self.__jogadores:
            valorJogador = jogador.getValorMao()
            cartasJogador = ", ".join([f"{c.getRank()} de {c.getSuit()}" for c in jogador.getCards()])

            prefixo = (
                f"🎴 **Resultado da Rodada** 🎴\n\n"
                f"👤 **Jogador {jogador.getNomeJogador()}**\n"
                f"Cartas: {cartasJogador}\n"
                f"Valor da mão: **{valorJogador}**\n\n"
                f"🤵 **Dealer**\n"
                f"Cartas: {cartasDealer}\n"
                f"Valor da mão: **{valorDealer}**\n\n"
            )

            # regras
            if len(jogador.getCards()) == 2 and valorJogador == 21 and len(self.__dealer.getCards()) == 2 and valorDealer == 21:
                mensagens.append(prefixo + "⚖️ Ambos têm **blackjack**. Resultado: **Empate!**")
                continue

            if len(jogador.getCards()) == 2 and valorJogador == 21:
                mensagens.append(prefixo + "🏆 Jogador tem **blackjack**! **Jogador ganhou!**")
                continue

            if len(self.__dealer.getCards()) == 2 and valorDealer == 21:
                mensagens.append(prefixo + "❌ Dealer tem **blackjack**! **Dealer ganhou!**")
                continue

            if valorJogador > 21:
                mensagens.append(prefixo + "💥 Jogador **estourou**! **Dealer ganhou!**")
                continue

            if valorDealer > 21:
                mensagens.append(prefixo + "💥 Dealer **estourou**! **Jogador ganhou!**")
                continue

            if valorJogador == valorDealer:
                mensagens.append(prefixo + "⚖️ **Empate!**")
                continue

            if valorJogador < valorDealer:
                mensagens.append(prefixo + "❌ **Dealer ganhou!**")
                continue

            if valorJogador > valorDealer:
                mensagens.append(prefixo + "🏆 **Jogador ganhou!**")
                continue

        self.__finalizarJogo()
        return "\n-----------------------------------------\n".join(mensagens)

    def getDict(self):
        return {
            "idJogo": self.__idJogo,
            "jogadorHost": {
                "id": self.__jogadorHost.getId(),
                "nome": self.__jogadorHost.getNomeJogador(),
                "valorMao": self.__jogadorHost.getValorMao(),
                "cartas": [c.getDict() for c in self.__jogadorHost.getCards()]
            } if self.__jogadorHost else None,
            "dealer": {
                "id": self.__dealer.getId(),
                "nome": self.__dealer.getNomeJogador(),
                "valorMao": self.__dealer.getValorMao(),
                "cartas": [c.getDict() for c in self.__dealer.getCards()]
            } if self.__dealer else None,
            "jogadores": [
                {
                    "id": jogador.getId(),
                    "nome": jogador.getNomeJogador(),
                    "valorMao": jogador.getValorMao(),
                    "cartas": [c.getDict() for c in jogador.getCards()]
                }
                for jogador in self.__jogadores
            ]
        }

    def __restateJogo(self, idJogador, nomeJogador):
        self.__jogadorHost = Jogador.newJogador(idJogador, nomeJogador)
        self.__jogadores.append(self.__jogadorHost)
        jogo = self.__blackjackRepo.consultarJogoIdJogador(idJogador)
        
        if jogo is None:
            raise Exception("Jogador ainda não está em nenhum jogo")
        
        self.__idJogo = jogo.getId()
        dealer = UsuarioRepo.newRepo().consultarPorUsuario("dealer")
        self.__dealer = Jogador.newJogador(dealer.getId(), "dealer")
        
        cartasJogoJogador = self.__cartaJogadorRepo.consultarCartasJogador(jogo.getId(), jogo.getIdJogador())
        cartasDealer = self.__cartaJogadorRepo.consultarCartasJogador(jogo.getId(), self.__dealer.getId())
        
        for carta in cartasJogoJogador:
            self.__jogadorHost.addCard(self.__baralho.deal(carta.getIdCarta()))
            
        for carta in cartasDealer:
            self.__dealer.addCard(self.__baralho.deal(carta.getIdCarta()))

    def __mensagemRetorno(self):
        cartasJogador = ", ".join([f"{c.getRank()} de {c.getSuit()}" for c in self.__jogadorHost.getCards()])
        cartasDealer = ", ".join([f"{c.getRank()} de {c.getSuit()}" for c in self.__dealer.getCards()])
        jogadasJogador = self.verificarJogadasJogador(self.__jogadorHost)

        retorno = (
            f"🎴 **Status da Rodada** 🎴\n\n"
            f"👤 **Jogador {self.__jogadorHost.getNomeJogador()}**\n"
            f"Cartas: {cartasJogador}\n"
            f"Valor da mão: **{self.__jogadorHost.getValorMao()}**\n\n"
            f"🤵 **Dealer**\n"
            f"Cartas: {cartasDealer}\n"
            f"Valor da mão: **{self.__dealer.getValorMao()}**\n\n"
            f"✨ **Jogadas possíveis**: {jogadasJogador if jogadasJogador else 'Nenhuma'}"
        )

        return retorno

    def __jogadaDealer(self):
        while self.verificarDealerPodeContinuar():
            self.__dealer.addCard(self.__baralho.deal())

    def __finalizarJogo(self):
        self.__cartaJogadorRepo.deletarTodasCartasJogo(self.__idJogo)
        self.__blackjackRepo.deleteJogo(self.__idJogo)
    
    @staticmethod
    def __gerarImagemCartas(cartas, caminhoSaida="mesaBlackjack.png"):
        """
        Gera uma imagem final juntando todas as imagens das cartas recebidas.
        Usa o método carta.getCaminhoImagem() para buscar os arquivos.
        """

        imagens = [Image.open(carta.getCaminhoImagem()) for carta in cartas]

        # Dimensões de cada carta
        larguraCarta, alturaCarta = imagens[0].size

        # Espaço entre cartas
        espacamento = 25

        # Tamanho da imagem final
        larguraFinal = len(imagens) * larguraCarta + (len(imagens) - 1) * espacamento
        alturaFinal = alturaCarta

        # Criar fundo verde estilo mesa
        mesa = Image.new("RGB", (larguraFinal, alturaFinal), (8, 100, 48))

        # Posicionar cartas
        x = 0
        for img in imagens:
            mesa.paste(img, (x, 0))
            x += larguraCarta + espacamento

        mesa.save(caminhoSaida)
        return caminhoSaida
        
        
        
        
        