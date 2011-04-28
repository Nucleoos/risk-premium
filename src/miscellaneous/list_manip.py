'''
Created on Feb 20, 2011

@author: t-bone
'''
def distinct(list):
    distinct_results = []
    for obj in list:
        if obj not in distinct_results:
            distinct_results.append(obj)
    return distinct_results