import os

def providePosList(path, ending=None):
    if not ending:
        ending = '.pos.npy'
    
    fileList  = []
    for root,  dirs,  files in os.walk(path):
        for f in files:
            if f.endswith(ending):
                path = root + '/' + f
                fileList.append(path)
                
    fileList = sorted(fileList)
    return fileList