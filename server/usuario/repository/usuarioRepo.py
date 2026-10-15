import sqlite3
import uuid
from configs.configs import Configs

from server.usuario.model.usuario import Usuario

class UsuarioRepo:
    def __init__(self, conn: sqlite3.Connection):
        self.__conn = conn
        self.__cursor = conn.cursor()
        
    @classmethod
    def newRepo(cls):
        return cls(sqlite3.Connection(Configs.newConfigs().getCaminhoDB(), check_same_thread=False))
        
    def consultarTodos(self):
        self.__cursor.execute("SELECT * FROM USUARIOS;")
        return [Usuario.newUsuario(usuario) for usuario in self.__formatar()]
    
    def consultaPorId(self, id: int):
        self.__cursor.execute("SELECT * FROM USUARIOS WHERE ID = ?", (id, ))
        dados = self.__formatar()
        
        if len(dados) <= 0:
            return
        
        return Usuario.newUsuario(dados[0])
    
    def consultarPorUsuario(self, usuario: str):
        self.__cursor.execute("SELECT * FROM USUARIOS WHERE USUARIO = ?", (usuario, ))
        dados = self.__formatar()
        
        if len(dados) <= 0:
            return
        
        return Usuario.newUsuario(dados[0])
    
    def login(self, usuario, senha):
        self.__cursor.execute("SELECT * FROM USUARIOS WHERE USUARIO = ? AND SENHA = ?", (usuario, senha))
        return self.__formatar()
    
    def create(self, usuarioCreate: Usuario):
        if usuarioCreate.getUsuario() == "dealer":
            raise Exception("Usuário não pode se chamar dealer")
        
        self.__cursor.execute("INSERT INTO USUARIOS (ID,  USUARIO, SENHA, SALDO) VALUES(?, ?, ?, 0)",
                              (usuarioCreate.getId(), usuarioCreate.getUsuario(), usuarioCreate.getSenha()))
        
        self.__conn.commit()
        return self.consultarTodos()
    
    def criarDealer(self):
        """Cria o usuário dealer. Usado para repor a base quando ele não existe."""
        self.__cursor.execute("INSERT INTO USUARIOS (ID, USUARIO, SENHA, SALDO) VALUES(?, ?, ?, 0)",
                              (None, "dealer", str(uuid.uuid4())))
        self.__conn.commit()
        return self.consultarPorUsuario("dealer")

    def update(self, usuarioUpdate: Usuario):
        usuario = self.consultaPorId(usuarioUpdate.getId())
        
        self.__cursor.execute("UPDATE USUARIOS SET USUARIO = ?, SENHA = ?, SALDO = ? WHERE ID = ?", 
                              (usuario.getUsuario(), usuario.getSenha(), usuarioUpdate.getSaldo(), usuario.getId()))

        self.__conn.commit()
        return self.consultarTodos()
    
    def delete(self, id: int):
        self.consultaPorId()
        self.__cursor.execute("DELETE FROM USUARIOS WHERE ID = ?", (id, ))
        self.__conn.commit()
        
        return self.consultarTodos()
        
    def __formatar(self):
        headers = [desc[0].lower() for desc in self.__cursor.description]
        dadosFormatados = [dict(zip(headers, data)) for data in self.__cursor.fetchall()]
        return dadosFormatados