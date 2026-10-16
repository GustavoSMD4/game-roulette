"""Regras do truco mineiro: baralho limpo, força das cartas, vazas e valores da mão.

Fica separado da mesa ao vivo para poder ser lido (e conferido) sem banco nem relógio.
"""
import random

NAIPES = ("spades", "hearts", "clubs", "diamonds")
RANKS = ("ace", "2", "3", "4", "5", "6", "7", "jack", "queen", "king")

# Manilhas do truco mineiro, da mais forte para a mais fraca
MANILHAS = {
    ("4", "clubs"): 14,      # zap (4 de paus)
    ("7", "hearts"): 13,     # 7 de copas
    ("ace", "spades"): 12,   # espadilha (ás de espadas)
    ("7", "diamonds"): 11    # 7 de ouros
}

# Força das cartas comuns: 3 > 2 > A > K > J > Q > 7 > 6 > 5 > 4
FORCAS = {
    "3": 10,
    "2": 9,
    "ace": 8,
    "king": 7,
    "jack": 6,
    "queen": 5,
    "7": 4,
    "6": 3,
    "5": 2,
    "4": 1
}

VALOR_NORMAL = 2
VALOR_TRUCO = 4
VALOR_RETRUCO = 8
VALOR_MAO_DEZ = 10
VALOR_MAO_DOZE = 12
VALOR_FERRO = 2

PONTOS_PARTIDA = 12
PONTOS_MAO_DEZ = 10
PONTOS_MAO_DOZE = 11

EQUIPES = ("A", "B")


def forcaDaCarta(carta) -> int:
    """Força da carta dentro do truco mineiro (maior vence)."""
    chave = (carta.get("rank"), carta.get("suit"))

    if chave in MANILHAS:
        return MANILHAS[chave]

    return FORCAS.get(carta.get("rank"), 0)


def novaCarta(rank: str, suit: str) -> dict:
    return {
        "id": f"{rank}_{suit}",
        "rank": rank,
        "suit": suit,
        "nomeImagem": f"{rank}_of_{suit}.png"
    }


def baralhoLimpo(semente=None) -> list:
    """As 40 cartas do truco (sem 8, 9 e 10), embaralhadas com a semente da mão."""
    cartas = [novaCarta(rank, suit) for rank in RANKS for suit in NAIPES]
    random.Random(semente).shuffle(cartas)
    return cartas


def tipoDaMao(pontosA: int, pontosB: int) -> str:
    """normal, dez (um time com 10), doze (um time com 11) ou ferro (os dois com 10+)."""
    pontosA = int(pontosA or 0)
    pontosB = int(pontosB or 0)

    if pontosA >= PONTOS_MAO_DEZ and pontosB >= PONTOS_MAO_DEZ:
        return "ferro"

    if max(pontosA, pontosB) >= PONTOS_MAO_DOZE:
        return "doze"

    if max(pontosA, pontosB) >= PONTOS_MAO_DEZ:
        return "dez"

    return "normal"


def valorInicial(tipo: str) -> int:
    return {
        "ferro": VALOR_FERRO,
        "dez": VALOR_MAO_DEZ,
        "doze": VALOR_MAO_DOZE
    }.get(tipo, VALOR_NORMAL)


def permiteTruco(tipo: str, valorAtual: int):
    """Próximo valor se ainda cabe truco nesta mão, senão None.

    Nas mãos de dez, de doze e de ferro o valor já está definido pela partida
    (e quem está com 10 pontos não pode pedir truco).
    """
    if tipo != "normal":
        return None

    if valorAtual == VALOR_NORMAL:
        return VALOR_TRUCO

    if valorAtual == VALOR_TRUCO:
        return VALOR_RETRUCO

    return None


def vencedorDaVaza(jogadas: list, equipePorJogador: dict):
    """Equipe dona da carta mais forte da vaza, ou None quando empatou.

    Empate só existe quando a carta mais forte aparece nas duas equipes: dois parceiros
    jogando a mesma força não anulam a vaza.
    """
    if not jogadas:
        return None

    maior = max(forcaDaCarta(jogada["carta"]) for jogada in jogadas)
    equipes = {
        equipePorJogador.get(str(jogada["idJogador"]))
        for jogada in jogadas
        if forcaDaCarta(jogada["carta"]) == maior
    }
    equipes.discard(None)

    return equipes.pop() if len(equipes) == 1 else None


def maoDecidida(vazas: list) -> bool:
    """Diz se a mão já está resolvida e não precisa das cartas restantes.

    - três vazas jogadas: a mão está resolvida de qualquer jeito;
    - um time ganhou as duas primeiras vazas: a mão acaba ali;
    - empate na primeira vaza: a segunda é a última.
    """
    if not vazas:
        return False

    if len(vazas) >= 3:
        return True

    primeira = vazas[0]

    if primeira is None:
        return len(vazas) >= 2

    if len(vazas) >= 2:
        return vazas[1] == primeira

    return False


def vencedorDaMao(vazas: list, equipeMao: str):
    """Melhor de três com as regras da casa.

    - dois times com vazas ganhas: quem tem mais leva;
    - um a um: o critério de desempate é quem ganhou a primeira vaza;
    - uma vaza só para um time (as outras empataram): ele leva;
    - todas empatadas: leva quem era mão.
    """
    ganhadoras = [vaza for vaza in vazas if vaza]

    if not ganhadoras:
        return equipeMao

    for equipe in EQUIPES:
        if ganhadoras.count(equipe) >= 2:
            return equipe

    if len(ganhadoras) == 2:
        return vazas[0] or equipeMao

    return ganhadoras[0]
