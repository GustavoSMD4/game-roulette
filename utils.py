

from datetime import datetime, timedelta, timezone

FUSO_BRASILIA = timezone(timedelta(hours=-3))


def agoraBrasiliaData():
    """Data/hora atual no horário de Brasília (UTC-3) como datetime, para contas de tempo."""
    return datetime.now(FUSO_BRASILIA)


def agoraBrasilia():
    """Data/hora atual no horário de Brasília (UTC-3), no formato aceito pelo SQLite."""
    return agoraBrasiliaData().strftime("%Y-%m-%d %H:%M:%S")


def paraBrasiliaData(dataHora: str):
    """Converte um texto de data/hora gravado pelo agoraBrasilia() de volta para datetime."""
    if dataHora is None:
        return None

    if isinstance(dataHora, datetime):
        return dataHora if dataHora.tzinfo else dataHora.replace(tzinfo=FUSO_BRASILIA)

    return datetime.strptime(str(dataHora)[:19], "%Y-%m-%d %H:%M:%S").replace(tzinfo=FUSO_BRASILIA)


def formatarReal(valor: float):
    if not isinstance(valor, float):
        try:
            valor = float(valor)
        except Exception as e:
            raise Exception("Valor para formatar precisa ser float!")
    
    valor_formatado = "{:,.2f}".format(valor)
    valor_formatado = valor_formatado.replace(',', 'TEMP').replace('.', ',').replace('TEMP', '.')
    valor_formatado = f"R${valor_formatado}"
    
    return valor_formatado    
    