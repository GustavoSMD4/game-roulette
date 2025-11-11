import uuid


class Usuario:
    def __init__(self):
        self.__id: int = None
        self.__usuario: str = None
        self.__senha: str = None
        self.__saldo: int | float = None
        
    @classmethod
    def newUsuario(cls, req: dict | None = None):
        if req is None: 
            return cls()
        
        usuario = cls()
        usuario.setId(req.get("id"))
        usuario.setUsuario(req.get("usuario"))
        usuario.setSenha(req.get("senha"))
        usuario.setSaldo(req.get("saldo"))
        return usuario
    
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
