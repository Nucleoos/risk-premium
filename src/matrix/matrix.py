'''
Created on 2011-07-22

@author: t-bone
'''

class Matrix(list):

    #def __init__(self, *args, **kwargs):
    #    super(Matrix, self).__init__()
    
    def __add__(self,y):
        
        x=self
        z=Matrix()
        for i in range(len(x)):
            z.append(x[i]+y[i])
        
        return z
    
    def __sub__(self,y):
        
        x=self
        z=Matrix()
        for i in range(len(x)):
            z.append(x[i]-y[i])
        
        return z