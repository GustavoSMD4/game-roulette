

from datetime import datetime, timedelta, timezone

FUSO_BRASILIA = timezone(timedelta(hours=-3))


def agoraBrasilia():
    """Data/hora atual no horário de Brasília (UTC-3), no formato aceito pelo SQLite."""
    return datetime.now(FUSO_BRASILIA).strftime("%Y-%m-%d %H:%M:%S")


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
    