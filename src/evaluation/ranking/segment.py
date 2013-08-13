'''
This module allows for the calculation of the basic rank metrics that evaluate
on a segment level (i.e. one ranking list at a time)

Created on Nov 25, 2012

@author: Eleftherios Avramidis
'''

from math import log
import logging
from collections import namedtuple
from sentence.ranking import Ranking

"""""""""
Kendall tau
"""""""""

def kendall_tau_prob(tau, pairs):
    """
    Calculation of Kendall tau hypothesis testing based on scipy calculation
    @param tau: already calculated tau coefficient
    @type tau: float
    @param pairs: count of pairs
    @type pairs: int
    @return: the probability for the null hypothesis of X and Y being independent
    @rtype: float
    """
    import numpy as np
    from scipy import special
    try:
        svar = (4.0 * pairs + 10.0) / (9.0 * pairs * (pairs - 1))
    except:
        svar = 1
    try: 
        z = tau / np.sqrt(svar)
    except:
        z = 1
    return special.erfc(np.abs(z) / 1.4142136)


def kendall_tau(predicted_rank_vector, original_rank_vector, **kwargs):
    """
    This is the refined calculation of segment-level Kendall tau of predicted vs human ranking according to WMT12 (Birch et. al 2012)
    @param predicted_rank_vector: a list of integers representing the predicted ranks
    @type predicted_rank_vector: [str, ..] 
    @param original_rank_vector: the name of the attribute containing the human rank
    @type original_rank_vector: [str, ..]
    @kwarg ties: way of handling ties, passed to L{sentence.ranking.Ranking} object
    @type ties: string
    @return: the Kendall tau score,
     the probability for the null hypothesis of X and Y being independent
     the count of concordant pairs,
     the count of discordant pairs,
     the count of pairs used for calculating tau (excluding "invalid" pairs)
     the count of original ties,
     the count of predicted ties,
     the count of all pairs
    @rtype: namedtuple(float, float, int, int, int, int, int, int)
    """
    import itertools
    ties_handling = kwargs.setdefault('ties','ceiling')
    
    #do necessary normalization of rank vectors
    predicted_rank_vector = predicted_rank_vector.normalize(ties=ties_handling)
    original_rank_vector = original_rank_vector.normalize(ties=ties_handling)
    
    logging.debug("\n* Segment tau *")
    logging.debug("predicted vector: {}".format(predicted_rank_vector))
    logging.debug("original vector : {}".format(original_rank_vector))
    
    #default wmt implementation excludes ties from the human (original) ranks
    exclude_ties = kwargs.setdefault("exclude_ties", True)
    #ignore also predicted ties
    penalize_predicted_ties = kwargs.setdefault("penalize_predicted_ties", True)
    logging.debug("exclude_ties: {}".format(exclude_ties))
    
    #
    if kwargs.setdefault("invert_ranks", False):
        inv = -1.00
    else:
        inv = 1.00
    
    #construct tuples, which contain pairs of ranks
    predicted_pairs = [(float(i), float(j)) for i, j in itertools.combinations(predicted_rank_vector, 2)]
    original_pairs = [(inv*float(i), inv*float(j)) for i, j in itertools.combinations(original_rank_vector, 2)]
    
    concordant_count = 0
    discordant_count = 0
    
    original_ties = 0
    predicted_ties = 0
    pairs = 0
    
    #iterate over the pairs
    for original_pair, predicted_pair in zip(original_pairs, predicted_pairs):
        original_i, original_j = original_pair
        #invert original ranks if required
        
        predicted_i, predicted_j = predicted_pair
        
        logging.debug("%s\t%s", original_pair,  predicted_pair)
        
        #general statistics
        pairs +=1
        if original_i == original_j:
            original_ties +=1
        if predicted_i == predicted_j:
            predicted_ties += 1
        
        # don't include refs, human no-ranks (-1), human ties
        if original_i == -1 or original_j == -1: 
            pass
        #don't count ties on the original rank
        elif original_i == original_j and exclude_ties:
            pass
        #concordant
        elif (original_i > original_j and predicted_i > predicted_j) \
          or (original_i < original_j and predicted_i < predicted_j) \
          or (original_i == original_j and predicted_i == predicted_j):
            #the former line will be true only if ties are not excluded 
            concordant_count += 1
            logging.debug("\t\tCON")
        #ignore false predicted ties if requested
        elif (predicted_i == predicted_j and not penalize_predicted_ties):
            pass 
        else: 
            discordant_count += 1
            logging.debug("\t\tDIS")
    all_pairs_count = concordant_count + discordant_count

    logging.debug("original_ties = %d, predicted_ties = %d", original_ties, predicted_ties)   
    logging.debug("conc = %d, disc= %d", concordant_count, discordant_count) 
    
    try:
        tau = 1.00 * (concordant_count - discordant_count) / all_pairs_count
        logging.debug("tau = {0} - {1} / {0} + {1}".format(concordant_count, discordant_count))
        logging.debug("tau = {0} / {1}".format(concordant_count - discordant_count, all_pairs_count))
        
    except ZeroDivisionError:
        tau = None
        prob = None
    else:
        prob = kendall_tau_prob(tau, all_pairs_count)
    
    logging.debug("tau = {}, prob = {}\n".format(tau, prob))
    
    #wrap results in a named tuple
    Result = namedtuple('Result', ['tau', 'prob', 'concordant_count', 'discordant_count', 'all_pairs_count', 'original_ties', 'predicted_ties', 'pairs'])
    result = Result(tau, prob, concordant_count, discordant_count, all_pairs_count, original_ties, predicted_ties, pairs)
    
    return result 


"""""""""
DCG
"""""""""                    

def _calculate_gains(predicted_rank_vector, original_rank_vector, verbose=True):
    """
    Calculate the gain for each one of the predicted ranks
    @param predicted_rank_vector: list of integers representing the predicted ranks
    @type predicted_rank_vector: [int, ...]
    @param original_rank_vector: list of integers containing the original ranks
    @type original_rank_vector: [int, ...]
    @return: a list of gains, relevant to the DCG calculation
    @rtype: [float, ...]
    """
    
    #the original calculation 
    r = predicted_rank_vector
    n = len(original_rank_vector)
    
    #the relevance of each rank is inv proportional to its rank index
    l = [n-i+1 for i in original_rank_vector]
    
    
    expn = 2**n
    gains = [0]*n 

    #added this line to get high gain for lower rank values
#    r = r[::-1]
    for j in range(n):            
        gains[r[j]-1] = (2**l[j]-1.0)/expn

        logging.debug("j={}\nr[j]={}\nl[j]={}\n".format(j,r[j],l[j])) 
        logging.debug("gains[{}] = ".format(r[j]-1))
        logging.debug("\t(2**l[j]-1.0) / 2**n =")
        logging.debug("\t(2**{}-1.0) / 2**{}=".format(l[j], n))
        logging.debug("\t{} / {} =".format((2**l[j]-1.0),expn))
        logging.debug("{}".format((2**l[j]-1.0)/expn))
        logging.debug("gains = {}".format(gains))
    
    assert min(gains)>=0, 'Not all ranks present'
    return gains


def idcg(gains, k):
    """
    Calculate the Ideal Discounted Cumulative Gain, for the given vector of ranking gains
    @param gains: a list of integers pointing to the ranks
    @type gains: [float, ...]
    @param k: the DCG cut-off
    @type k: int
    @return: the calculated Ideal Discounted Cumulative Gain
    @rtype: float
    """
    #put the ranks in an order
    gains.sort()
    #invert the list
    gains = gains[::-1]
    ideal_dcg = sum([g/log(j+2) for (j,g) in enumerate(gains[:k])])
    return ideal_dcg


def ndgc_err(predicted_rank_vector, original_rank_vector, k=None):
    """
    Calculate the normalize Discounted Cumulative Gain and the Expected Reciprocal Rank on a sentence level
    This follows the definition of U{DCG<http://en.wikipedia.org/wiki/Discounted_cumulative_gain#Cumulative_Gain>} 
    and U{ERR<http://research.yahoo.com/files/err.pdf>}, and the implementation of 
    U{Yahoo Learning to Rank challenge<http://learningtorankchallenge.yahoo.com/evaluate.py.txt>}     
    @param predicted_rank_vector: list of integers representing the predicted ranks
    @type predicted_rank_vector: [int, ...]
    @param original_rank_vector: list of integers containing the original ranks.
    @type original_rank_vector: [int, ...]
    @param k: the cut-off for the calculation of the gains. If not specified, the length of the ranking is used
    @type k: int 
    @return: a tuple containing the values for the two metrics
    @rtype: tuple(float,float)
    """
    # Number of documents    
    
    r = predicted_rank_vector.normalize(ties='ceiling').integers()
    l = original_rank_vector.normalize(ties='ceiling').integers()
    n = len(l)
    
    #if user doesn't specify k, set equal to the ranking length
    if not k:
        k = n
    
    #make sure that the lists have the right dimensions 
    assert len(r)==n, 'Expected {} ranks, but got {}.'.format(n,len(r))    
    gains = _calculate_gains(r, l)
        
    #ERR calculations
    p = 1.0    
    err = 0.0
    for j in range(n):    
        r = gains[j]
        err += p*r/(j+1.0)
        p *= 1-r
    4
    #DCG calculation
    dcg = sum([g/log(j+2) for (j,g) in enumerate(gains[:k])])
    
    #NDCG calculation
    ideal_dcg = idcg(gains, k)
      
    if ideal_dcg:
        ndcg = dcg / ideal_dcg
    else:
        ndcg = 1.0
        
    return ndcg, err



"""
Reciprocal rank
"""

def reciprocal_rank(predicted_rank_vector, original_rank_vector, **kwargs):
    """
    Calculates the First Answer Reciprocal Rank according to Radev et. al (2002) 
    @param predicted_rank_vector: list of integers representing the predicted ranks
    @type predicted_rank_vector: [int, ...]
    @param original_rank_vector: list of integers containing the original ranks.
    @type original_rank_vector: [int, ...]
    @kwarg ties: way of handling ties, passed to L{sentence.ranking.Ranking} object
    @type ties: string
    @return: the reciprocal rank value
    @type: float
    """
    ties_handling = kwargs.setdefault('ties','ceiling')
    
    predicted_rank_vector = predicted_rank_vector.normalize(ties=ties_handling)
    original_rank_vector = original_rank_vector.normalize(ties=ties_handling)
    
    best_original_rank = min(original_rank_vector)    
    best_original_rank_indexes = original_rank_vector.indexes(best_original_rank)
    
    predicted_values_for_best_rank = [predicted_rank_vector[index] for index in best_original_rank_indexes]
    
    #if there is a tie for the best rank, this will return our best choice for it
    best_predicted_value_for_best_rank = min(predicted_values_for_best_rank)
    
    reciprocal_rank = 1.00/best_predicted_value_for_best_rank
    return reciprocal_rank


            
#if __name__ == "__main__":
#    predicted_rank_vector = Ranking([1,3,2.2,"0.1"])
#    print predicted_rank_vector.normalize()
#    original_rank_vector =  Ranking([1,2,3,4])
##    dcg, err = ndgc_err(predicted_rank_vector, original_rank_vector, 4)
##    print "ERR = {}\n nDCG_p = {}".format(dcg, err) 
#    
#    print ndgc_err(predicted_rank_vector, original_rank_vector)
    
    
    
        
     
    
    