import threading

from utils import agoraBrasiliaData

# Presença nas mesas: quem está com a mesa aberta agora. Fica só na memória do servidor,
# igual ao chat, e é descartado quando a sessão termina.
ATIVO_SEGUNDOS = 25

_CADEADO = threading.Lock()
_PRESENCAS = {}


def __chave(codigo):
    return str(codigo or "").strip().upper()


def marcar(codigo: str, idJogador, nome: str):
    """Registra que o jogador está com a mesa aberta neste instante."""
    if idJogador is None:
        return

    with _CADEADO:
        sessao = _PRESENCAS.setdefault(__chave(codigo), {})
        sessao[str(idJogador)] = {
            "idJogador": str(idJogador),
            "nome": str(nome or "Jogador"),
            "visto": agoraBrasiliaData()
        }


def presentes(codigo: str, segundos: int = ATIVO_SEGUNDOS):
    """Jogadores vistos nos últimos segundos, do mais recente para o mais antigo."""
    agora = agoraBrasiliaData()

    with _CADEADO:
        sessao = list(_PRESENCAS.get(__chave(codigo), {}).values())

    ativos = [
        jogador for jogador in sessao
        if (agora - jogador["visto"]).total_seconds() <= segundos
    ]

    return [
        {"idJogador": jogador["idJogador"], "nome": jogador["nome"], "segundos": int((agora - jogador["visto"]).total_seconds())}
        for jogador in sorted(ativos, key=lambda item: item["visto"], reverse=True)
    ]


def limpar(codigo: str):
    with _CADEADO:
        _PRESENCAS.pop(__chave(codigo), None)


def quantidade(codigo: str) -> int:
    return len(presentes(codigo))
