import uuid


class Usuario:
    def __init__(self, id: int | str, usuario: str, senha: str, saldo: float):
        self.__id = id
        self.__usuario = usuario
        self.__senha = senha
        self.__saldo = saldo
        
    @classmethod
    def usuario(cls, req: dict | None = None):
        if req is None: 
            return cls("", "", "", 0)
        
        id = req.get("id") if req.get("id") else str(uuid.uuid4())
        return cls(id, req.get("usuario"), req.get("senha"), req.get("saldo"))
    
    def getDictUsuario(self):
        return dict(usuario=self.__usuario, saldo=self.__saldo)

    def getId(self):
        return self.__id

    def getUsuario(self):
        return self.__usuario

    def getSenha(self):
        return self.__senha

    def getSaldo(self):
        return self.__saldo

    def setId(self, id):
        self.__id = id

    def setUsuario(self, usuario):
        self.__usuario = usuario

    def setSenha(self, senha):
        self.__senha = senha

    def setSaldo(self, saldo):
        self.__saldo = saldo
