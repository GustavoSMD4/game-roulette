

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
    