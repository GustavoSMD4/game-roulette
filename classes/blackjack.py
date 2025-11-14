from classes.baralhoFromDb import BaralhoDb
from classes.jogador import Jogador
from server.blackjack.models.blackjackModel import BlackjackModel
from server.blackjack.repository.blackjackRepo import BlackjackRepo
from server.blackjack.repository.cartaJogadorBlackjackRepo import CartaJogadorBlackjackRepo
from server.usuario.repository.usuarioRepo import UsuarioRepo

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
        
        cartasJogador = ", ".join([f"{c.getRank()} de {c.getSuit()}" for c in blackjack.__jogadorHost.getCards()])
        cartasDealer = ", ".join([f"{c.getRank()} de {c.getSuit()}" for c in blackjack.__dealer.getCards()])
        jogadasJogador = blackjack.verificarJogadasJogador(blackjack.__jogadorHost)
        
        retorno = (
            f"Jogador {blackjack.__jogadorHost.getNomeJogador()} tem: {cartasJogador} "
            f"(valor da mão: {blackjack.__jogadorHost.getValorMao()})\n"
            f"Dealer tem: {cartasDealer} "
            f"(valor da mão: {blackjack.__dealer.getValorMao()})\n"
            f"Jogadas possíveis: {jogadasJogador if jogadasJogador else 'Nenhuma'}"
        )
        
        return retorno
    
    @classmethod
    def restateJogo(cls, idJogador, nomeJogador):
        blackjack = cls()
        blackjack.__jogadorHost = Jogador.newJogador(idJogador, nomeJogador)
        jogo = blackjack.__blackjackRepo.consultarJogoIdJogador(idJogador)
        blackjack.__idJogo = jogo.getId()
        dealer = UsuarioRepo.newRepo().consultarPorUsuario("dealer")
        blackjack.__dealer = Jogador.newJogador(dealer.getId(), "dealer")
        
        cartasJogoJogador = blackjack.__cartaJogadorRepo.consultarCartasJogador(jogo.getId(), jogo.getIdJogador())
        cartasDealer = blackjack.__cartaJogadorRepo.consultarCartasJogador(jogo.getId(), blackjack.__dealer.getId())
        
        for carta in cartasJogoJogador:
            blackjack.__jogadorHost.addCard(blackjack.__baralho.deal(carta.getIdCarta()))
            
        for carta in cartasDealer:
            blackjack.__dealer.addCard(blackjack.__baralho.deal(carta.getIdCarta()))
        
        cartasJogador = ", ".join([f"{c.getRank()} de {c.getSuit()}" for c in blackjack.__jogadorHost.getCards()])
        cartasDealer = ", ".join([f"{c.getRank()} de {c.getSuit()}" for c in blackjack.__dealer.getCards()])
        jogadasJogador = blackjack.verificarJogadasJogador(blackjack.__jogadorHost)
        
        retorno = (
            f"Jogador {blackjack.__jogadorHost.getNomeJogador()} tem: {cartasJogador} "
            f"(valor da mão: {blackjack.__jogadorHost.getValorMao()})\n"
            f"Dealer tem: {cartasDealer} "
            f"(valor da mão: {blackjack.__dealer.getValorMao()})\n"
            f"Jogadas possíveis: {jogadasJogador if jogadasJogador else 'Nenhuma'}"
        )
        
        return retorno
    
    @classmethod
    def jogadaJogador(cls, idJogador, nomeJogador, jogada: int):
        blackjack = cls()
        blackjack.restateJogo(idJogador, nomeJogador)
        
        if jogada not in [1, 2, 3]:
            raise Exception("Jogada aceita somente números 1, 2 e 3")
        
        if jogada not in blackjack.__jogadasJogador:
            raise Exception("Jogador não pode realizar essa jogada")
        
        if jogada == 1:
            blackjack.__jogadorHost.addCard(blackjack.__baralho.deal())
            
        if jogada == 2:
            blackjack.__jogadorHost.addCard(blackjack.__baralho.deal())
            blackjack.__jogadaDealer()
            
        if jogada == 3:
            raise Exception("Ainda não implementado")

    def getIdJogo(self):
        return self.__idJogo

    def addJogador(self, jogador: Jogador):
        for joga in self.__jogadores:
            if joga.getId() == jogador.getId():
                raise Exception(f"Jogador {jogador.getNomeJogador()} já está no jogo")
            
        self.__jogadores.append(jogador)

    def jogadaJogador(self, jogador: Jogador):
        if jogador.getCards() == 2 and jogador.getValorMao() == 21:
            return f"{jogador.getNomeJogador()} tem Blackjack!"
        
        return self.verificarJogadorPodeContinuar(jogador)
    
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

        if comprar:
            self.__jogadasJogador.append(1)
            opcoes.append("1")
        if dobrar:
            self.__jogadasJogador.append(2)
            opcoes.append("2")
        if dividir:
            self.__jogadasJogador.append(3)
            opcoes.append("3")

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
        resultado: list[dict] = []
        
        for jogador in self.__jogadores:
            if len(jogador.getCards()) == 2 and jogador.getValorMao() == 21:
                if len(self.__dealer.getCards()) == 2 and self.__dealer.getValorMao() == 21:
                    resultado.append({
                        "message": f"{jogador.getNomeJogador()} tem blackjack, __ tem blackjack, empate!",
                        "ganhou": 2,
                        "valor": 0
                    })

            if len(jogador.getCards()) == 2 and jogador.getValorMao() == 21:
                resultado.append({
                    "message": f"{jogador.getNomeJogador()} tem blackjack, dealer tem {self.__dealer.getValorMao()}, jogador ganhou!",
                    "ganhou": 1,
                    "valor": (jogador.getValorAposta() * 1.5)
                })

            if len(self.__dealer.getCards()) == 2 and self.__dealer.getValorMao() == 21:
                resultado.append({
                    "message": f"{jogador.getNomeJogador()} tem {jogador.getValorMao()}, dealer tem blackjack, dealer ganhou!",
                    "ganhou": 0,
                    "valor": -jogador.getValorAposta()
                })

            if jogador.getValorMao() > 21:
                resultado.append({
                    "message": f"{jogador.getNomeJogador()} estourou, dealer Ganhou!",
                    "ganhou": 0,
                    "valor": -jogador.getValorAposta()
                })

            if jogador.getValorMao() <= 21 and self.__dealer.getValorMao() > 21:
                resultado.append({
                    "message": f"Dealer estourou, {jogador.getNomeJogador()} ganhou!",
                    "ganhou": 1,
                    "valor": jogador.getValorAposta()
                })

            if jogador.getValorMao() == self.__dealer.getValorMao():
                resultado.append({
                    "message": f"{jogador.getNomeJogador()} tem {jogador.getValorMao()}, Dealer tem {self.__dealer.getValorMao()}. Empate!",
                    "ganhou": 2,
                    "valor": 0
                })

            if jogador.getValorMao() < self.__dealer.getValorMao() and self.__dealer.getValorMao() <= 21:
                resultado.append({
                    "message": f"{jogador.getNomeJogador()} tem {jogador.getValorMao()}, Dealer tem {self.__dealer.getValorMao()}. Dealer ganhou!",
                    "ganhou": 0,
                    "valor": -jogador.getValorAposta()
                })

            if jogador.getValorMao() > self.__dealer.getValorMao() and self.__dealer.getValorMao() <= 21:
                resultado.append({
                    "message": f"{jogador.getNomeJogador()} tem {jogador.getValorMao()}, Dealer tem {self.__dealer.getValorMao()}. Jogador ganhou!",
                    "ganhou": 1,
                    "valor": jogador.getValorAposta()
                })

        resultado.append({
            "message": "Resultado inesperado.",
            "ganhou": 2,
            "valor": 0
        })
        
        return resultado

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

    def __jogadaDealer(self):
        while self.verificarDealerPodeContinuar():
            self.__dealer.addCard(self.__baralho.deal())
