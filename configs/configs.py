
class Configs:
    def __init__(self):
        self.__caminhoDB = "database/database.db"
        
    @classmethod
    def newConfigs(cls):
        return cls()
    
    def getCaminhoDB(self):
        return self.__caminhoDB