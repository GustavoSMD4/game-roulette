

import uuid
from server.usuario.model.usuario import Usuario
from server.usuario.repository.usuarioRepo import UsuarioRepo


class UsuarioService:
    def __init__(self, repository: UsuarioRepo):
        self.__repository = repository
        
    @classmethod
    def newService(cls):
        return cls(UsuarioRepo.newRepo())
    
    def verificarUsuario(self, req: dict):
        idUsuario = req.get("idUsuario")
        nomeUsuario = req.get("nomeUsuario")
        usuario = self.__repository.consultaPorId(idUsuario)
        
        if usuario is None:
            newUsuario = Usuario.newUsuario()
            newUsuario.setId(idUsuario)
            newUsuario.setUsuario(nomeUsuario)
            newUsuario.setSenha(str(uuid.uuid4()))
            newUsuario.setSaldo(0)
            usuarios = self.__repository.create(newUsuario)
            return next((usuario for usuario in usuarios if usuario.getId() == idUsuario))
        
        else:
            usuario.setUsuario(nomeUsuario)
            self.__repository.update(usuario)
            return usuario
            
    def depositar(self, req: dict):
        valorAdicionar = req.get("saldo")
        
        if float(valorAdicionar) > 1000000:
            raise Exception("Valor máximo por deposito é de 1.000.000")
        
        if float(valorAdicionar) <= 0:
            raise Exception("Valor para depositar precisa ser maior que 0")
        
        usuario = self.verificarUsuario(req)
        saldoAtual = usuario.getSaldo()
        usuario.setSaldo(req.get("saldo") + saldoAtual)
        self.__repository.update(usuario)
        return usuario
        
            
        


