import uuid


class BlackjackModel:
    def __init__(self, id: str):
        self.__id = id
        
    @classmethod
    def newBlackjackModel(cls, id = None):
        if id is None:
            id = str(uuid.uuid4())
        
        return cls(id)
    
    def getId(self):
        return self.__id