'''
Created on 22 May 2013

@author: Eleftherios Avramidis
'''

import sys
from collections import OrderedDict
from io_utils.input.jcmlreader import JcmlReader
from ranking.set import allmetrics
from sentence.ranking import Ranking


def _display(dic):
    dic = OrderedDict(sorted(dic.items(), key=lambda t: t[0]))
    for key, value in dic.iteritems():
        print "{}\t{}".format(key,value)
    


if __name__ == '__main__':
    
    if len(sys.argv)<4:
        sys.stderr.write("Commandline options: \npython rankeval.py <filename> <predicted_rank_name> <gold_rank_name>\n")
    
    
    filename = sys.argv[1]
    predicted_rank_name = sys.argv[2]
    gold_rank_name = sys.argv[3]
    
    gold_ranklist = []
    predicted_ranklist = []
    
    #get all ranks in a list
    for parallelsentence in JcmlReader(filename).get_parallelsentences(): 
        
        gold_ranks = Ranking(parallelsentence.get_target_attribute_values(gold_rank_name))
        gold_ranklist.append(gold_ranks)
        
        predicted_ranks = Ranking(parallelsentence.get_target_attribute_values(predicted_rank_name))
        predicted_ranklist.append(predicted_ranks)
        
    _display(allmetrics (predicted_ranklist, gold_ranklist))
    
        
    