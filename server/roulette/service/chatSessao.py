import threading
from collections import deque

from utils import agoraBrasiliaData

# Chat das mesas privadas: fica só na memória do servidor, existe enquanto a sessão existir
# e é descartado quando a sessão expira. Nada é gravado no banco.
LIMITE_MENSAGENS = 200
LIMITE_TEXTO = 200
LIMITE_INICIAL = 20

_CADEADO = threading.Lock()
_SESSOES = {}
_ULTIMO_ID = 0


class MensagemInvalida(Exception):
    pass


def enviar(codigo: str, idJogador, nome: str, texto: str):
    global _ULTIMO_ID

    codigo = str(codigo or "").strip().upper()
    conteudo = " ".join(str(texto or "").split())

    if not codigo:
        raise MensagemInvalida("Sessão inválida")

    if not conteudo:
        raise MensagemInvalida("Escreva uma mensagem")

    if len(conteudo) > LIMITE_TEXTO:
        raise MensagemInvalida(f"Mensagem muito longa (máximo {LIMITE_TEXTO} caracteres)")

    with _CADEADO:
        _ULTIMO_ID += 1
        mensagem = {
            "id": _ULTIMO_ID,
            "idJogador": str(idJogador) if idJogador is not None else None,
            "nome": str(nome or "Jogador"),
            "texto": conteudo,
            "hora": agoraBrasiliaData().strftime("%H:%M")
        }
        _SESSOES.setdefault(codigo, deque(maxlen=LIMITE_MENSAGENS)).append(mensagem)

    return mensagem


def novas(codigo: str, desde: int = 0, limite: int = 50):
    """Devolve as mensagens novas a partir de um id. Sem id informado, devolve o fim da conversa."""
    codigo = str(codigo or "").strip().upper()

    if not codigo:
        return []

    with _CADEADO:
        mensagens = list(_SESSOES.get(codigo, ()))

    if desde and int(desde) > 0:
        return [mensagem for mensagem in mensagens if mensagem["id"] > int(desde)][:limite]

    return mensagens[-min(limite, LIMITE_INICIAL):]


def limpar(codigo: str):
    with _CADEADO:
        _SESSOES.pop(str(codigo or "").strip().upper(), None)


def quantidade(codigo: str) -> int:
    with _CADEADO:
        return len(_SESSOES.get(str(codigo or "").strip().upper(), ()))
