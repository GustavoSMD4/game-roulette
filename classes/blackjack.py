from classes.baralho import Baralho
from classes.baralhoFromDb import BaralhoDb
from classes.jogador import Jogador
from server.blackjack.models.blackjackModel import BlackjackModel
from server.blackjack.repository.blackjackRepo import BlackjackRepo
from server.blackjack.repository.cartaJogadorBlackjackRepo import CartaJogadorBlackjackRepo
from server.usuario.repository.usuarioRepo import UsuarioRepo

class Blackjack:
    def __init__(self, jogadorHost: Jogador, qtdeBaralhos: int = 4):
        self.__idJogo = None
        self.__baralho = BaralhoDb.newBaralhoFromDb(qtdeBaralhos)
        self.__jogadorHost = jogadorHost
        self.__jogadores: list[Jogador] = []
        self.__dealer: Jogador = None
        self.__blackjackRepo = BlackjackRepo.newBlackjackRepo()
        self.__cartaJogadorRepo = CartaJogadorBlackjackRepo.newRepo()
        
    def iniciarJogo(self):
        jogo = self.__blackjackRepo.consultarJogoIdJogador(self.__jogadorHost.getId())
        dealer = UsuarioRepo.newRepo().consultarPorUsuario("dealer")
        self.__dealer = Jogador.newJogador(dealer.getId(), "dealer")
        
        if jogo:
            raise Exception("O jogador já está em um jogo de blackjack")
        
        carta1Jogador = self.__baralho.deal()
        carta2Jogador = self.__baralho.deal()
        cartaDealer = self.__baralho.deal()
        self.__jogadorHost.addCard(carta1Jogador)
        self.__jogadorHost.addCard(carta2Jogador)
        self.__dealer.addCard(cartaDealer)
        self.__jogadores.append(self.__jogadorHost)
        jogoCriado = self.__blackjackRepo.createNovoJogo(BlackjackModel.newBlackjackModel(idJogadorHost=self.__jogadorHost.getId()))
        self.__idJogo = jogoCriado.getId()
        return self
        
    def restateJogo(self):
        jogo = self.__blackjackRepo.consultarJogoIdJogador(self.__jogadorHost.getId())
        dealer = UsuarioRepo.newRepo().consultarPorUsuario("dealer")
        self.__dealer = Jogador.newJogador(dealer.getId(), "dealer")
        cartasJogoJogador = self.__cartaJogadorRepo.consultarCartasJogador(jogo.getId(), jogo.getIdJogador())
        cartasDealer = self.__cartaJogadorRepo.consultarCartasJogador(jogo.getId(), self.__dealer.getId())
        
        for carta in cartasJogoJogador:
            self.__jogadorHost.addCard(self.__baralho.deal(carta.getId()))
            
        for carta in cartasDealer:
            self.__dealer.addCard(self.__baralho.deal(carta.getId()))
            
        return self

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



