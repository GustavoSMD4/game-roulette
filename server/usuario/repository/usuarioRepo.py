import sqlite3
from flask import jsonify

from server.usuario.model.usuario import Usuario

class UsuarioRepo:
    def __init__(self, conn: sqlite3.Connection):
        self.__conn = conn
        self.__cursor = conn.cursor()
        
    @classmethod
    def usuarioRepo(cls):
        return cls(sqlite3.Connection("database/database.db", check_same_thread=False))
        
    def consultarTodos(self):
        self.__cursor.execute("SELECT * FROM USUARIOS;")
        return self.__formatar()
    
    def consultaPorId(self, id: int):
        self.__cursor.execute("SELECT * FROM USUARIOS WHERE ID = ?", (id, ))
        dados = self.__formatar()
        return Usuario.usuario(dados[0])
    
    def consultarPorUsuario(self, usuario: str):
        self.__cursor.execute("SELECT * FROM USUARIOS WHERE USUARIO = ?", (usuario, ))
        dados = self.__formatar()
        return Usuario.usuario(dados[0])
    
    def create(self, usuarioCreate: Usuario):
        self.__cursor.execute("INSERT INTO USUARIOS (USUARIO, SENHA, SALDO) VALUES(?, ?, ?)",
                              (usuarioCreate.getUsuario(), usuarioCreate.getSenha(), usuarioCreate.getSaldo()))
        
        self.__conn.commit()
        
        return self.consultarTodos()
    
    def update(self, usuarioUpdate: Usuario):
        if usuarioUpdate.getId() is None or usuarioUpdate.getId() == "":
            return jsonify({"error": "id vazio"}), 400
        
        self.consultaPorId(usuarioUpdate.getId())
        self.__cursor.execute("UPDATE USUARIOS SET USUARIO = ?, SENHA = ?, SALDO = ? WHERE ID = ?", 
                              (usuarioUpdate.getUsuario(), usuarioUpdate.getSenha(), usuarioUpdate.getSaldo(), usuarioUpdate.getId()))

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