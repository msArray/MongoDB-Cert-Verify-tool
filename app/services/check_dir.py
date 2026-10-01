import os

def checkDir(path) -> bool | list[str]:
    if(not os.path.exists(path)):
        return False
    
    if(len(os.listdir(path)) == 0):
        return False
    
    return os.listdir(path)