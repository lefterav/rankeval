'''
This module allows for the calculation of the basic rank metrics that evaluate
on a segment level (i.e. one ranking list at a time)

Created on 18 Dec 2012

@author: Eleftherios Avramidis
'''

import segment
from numpy import average
import numpy as np

def kendall_tau_set(predicted_rank_vectors, original_rank_vectors, **kwargs):
    """
    This is the refined calculation of set-level Kendall tau of predicted vs human ranking according to WMT12 (Birch et. al 2012)
    It returns both set-level Kendall tau and average segment-level Kendall tau
    @param predicted_rank_vectors: a list of lists containing integers representing the predicted ranks, one ranking for each segment
    @type predicted_rank_vectors: [Ranking, ..] 
    @param original_rank_vectors:  a list of the names of the attribute containing the human rank, one ranking for each segment
    @type original_rank_vectors: [Ranking, ..] 
    @return: overall Kendall tau score,
      - average segment Kendall tau score,
      - the probability for the null hypothesis of X and Y being independent
      - the count of concordant pairs,
      - the count of discordant pairs,
      - the count of pairs used for calculating tau (excluding "invalid" pairs)
      - the count of original ties,
      - the count of predicted ties,
      - the count of all pairs
    @rtype: {string:float, string:float, string:int, string:int, string:int, string:int, string:int, string:int}
    
    """
    segtaus = []
    segprobs = []
    
    concordant = 0
    discordant = 0
    valid_pairs = 0
    original_ties_overall = 0
    predicted_ties_overall = 0
    pairs_overall = 0
    sentences_with_ties = 0
    
    for predicted_rank_vector, original_rank_vector in zip(predicted_rank_vectors, original_rank_vectors):
        
        
        segtau, segprob, concordant_count, discordant_count, all_pairs_count, original_ties, predicted_ties, pairs = segment.kendall_tau(predicted_rank_vector, original_rank_vector, **kwargs)
        
        if segtau and segprob:
            segtaus.append(segtau)
            segprobs.append(segprob)
            
        concordant += concordant_count
        discordant += discordant_count
        valid_pairs += all_pairs_count
        
        original_ties_overall += original_ties
        predicted_ties_overall += predicted_ties
        if predicted_ties > 0:
            sentences_with_ties += 1
        pairs_overall += pairs
    
    
    tau = 1.00 * (concordant - discordant) / (concordant + discordant)
    prob = segment.kendall_tau_prob(tau, valid_pairs)
    
    avg_seg_tau = np.average(segtaus)               
    avg_seg_prob = np.product(segprobs)
    
    predicted_ties_avg = 100.00*predicted_ties / pairs_overall
    sentence_ties_avg = 100.00*sentences_with_ties / len(predicted_rank_vector)
    
    stats = {'tau': tau,
             'tau_prob': prob,
             'tau_avg_seg': avg_seg_tau,
             'tau_avg_seg_prob': avg_seg_prob,
             'tau_concordant': concordant,
             'tau_discordant': discordant,
             'tau_valid_pairs': valid_pairs,
             'tau_all_pairs': pairs_overall,
             'tau_original_ties': original_ties_overall,
             'tau_predicted_ties': predicted_ties_overall,
             'tau_predicted_ties_per': predicted_ties_avg,
             'tau_sentence_ties': sentences_with_ties,
             'tau_sentence_ties_per' : sentence_ties_avg
             
             }

    return stats


def mrr(predicted_rank_vectors, original_rank_vectors, **kwargs):
    """
    Calculation of mean reciprocal rank based on Radev et. all (2002)
    @param predicted_rank_vectors: a list of lists containing integers representing the predicted ranks, one ranking for each segment
    @type predicted_rank_vectors: [Ranking, ..] 
    @param original_rank_vectors:  a list of the names of the attribute containing the human rank, one ranking for each segment
    @type original_rank_vectors: [Ranking, ..]
    @return: mean reciprocal rank
    @rtype: {string, float} 
    """
    reciprocal_ranks = []
    
    for predicted_rank_vector, original_rank_vector in zip(predicted_rank_vectors, original_rank_vectors):
        reciprocal_rank = segment.reciprocal_rank(predicted_rank_vector, original_rank_vector)        
        reciprocal_ranks.append(reciprocal_rank)
                
    return {'mrr' : average(reciprocal_ranks)}


def best_predicted_vs_human(predicted_rank_vectors, original_rank_vectors):
    """
    For each sentence, the item selected as best by our system, may have been ranked lower by the humans. This 
    statistic counts how many times the item predicted as best has fallen into each of the human ranks.
    This is useful for plotting. 
    @param predicted_rank_vectors: a list of lists containing integers representing the predicted ranks, one ranking for each segment
    @type predicted_rank_vectors: [Ranking, ..] 
    @param original_rank_vectors:  a list of the names of the attribute containing the human rank, one ranking for each segment
    @type original_rank_vectors: [Ranking, ..]
    @return: a dictionary with percentages for each human rank
    @rtype: {string, float}
    """
    actual_values_of_best_predicted = {}
    for predicted_rank_vector, original_rank_vector in zip(predicted_rank_vectors, original_rank_vectors):
        
        #make sure vectors are normalized
        predicted_rank_vector = predicted_rank_vector.normalize()
        original_rank_vector = original_rank_vector.normalize()
        if not predicted_rank_vector:
            continue
        best_predicted_rank = min(predicted_rank_vector)
        
        original_ranks = []
        for original_rank, predicted_rank in zip(original_rank_vector, predicted_rank_vector):
            if predicted_rank == best_predicted_rank:
                original_ranks.append(original_rank)
        
        #if best rank given to many items, get the worst human rank for it
        selected_original_rank = max(original_ranks)
        a = actual_values_of_best_predicted.setdefault(selected_original_rank, 0)
        actual_values_of_best_predicted[selected_original_rank] = a + 1

    n = len(predicted_rank_vectors)
    percentages = {}
    total = 0
    #gather everything into a dictionary
    for rank, counts in  actual_values_of_best_predicted.iteritems():
        percentages["bph_" + str(rank)] = round(100.00 * counts / n , 2 )
        total += counts
    return percentages

def avg_predicted_ranked(predicted_rank_vectors, original_rank_vectors, **kwargs):
    
    """
    It will provide the average human rank of the item chosen by the system as best
    @param predicted_rank_vectors: a list of lists containing integers representing the predicted ranks, one ranking for each segment
    @type predicted_rank_vectors: [Ranking, ..] 
    @param original_rank_vectors:  a list of the names of the attribute containing the human rank, one ranking for each segment
    @type original_rank_vectors: [Ranking, ..]
    @return: a dictionary with the name of the metric and its value
    @rtype: {string, float}
    """
    
    original_ranks = []
    
    for predicted_rank_vector, original_rank_vector in zip(predicted_rank_vectors, original_rank_vectors):        
        
        #make sure vectors are normalized
        predicted_rank_vector = predicted_rank_vector.normalize(ties='ceiling')
        original_rank_vector = original_rank_vector.normalize(ties='ceiling')
        
        best_predicted_rank = min(predicted_rank_vector)
        mapped_original_ranks = []
        
        for original_rank, predicted_rank in zip(original_rank_vector, predicted_rank_vector):
            if predicted_rank == best_predicted_rank:
                mapped_original_ranks.append(original_rank)
        
        #in case of ties get the worst one
        original_ranks.append(max(mapped_original_ranks))
    
    return {'avg_predicted_ranked': average(original_ranks)}
        
        


def avg_ndgc_err(predicted_rank_vectors, original_rank_vectors, **kwargs):
    """
    Returns normalize Discounted Cumulative Gain and the Expected Reciprocal Rank, both averaged over number of sentences
    @param predicted_rank_vectors: a list of lists containing integers representing the predicted ranks, one ranking for each segment
    @type predicted_rank_vectors: [Ranking, ..] 
    @param original_rank_vectors:  a list of the names of the attribute containing the human rank, one ranking for each segment
    @type original_rank_vectors: [Ranking, ..]
    @keyword k: cut-off passed to the segment L{ndgc_err} function
    @type k: int 
    @return: a dictionary with the name of the metric and the respective result
    @rtype: {string, float}
    """
    ndgc_list = []
    err_list = []
    for predicted_rank_vector, original_rank_vector in zip(predicted_rank_vectors, original_rank_vectors):
        k = kwargs.setdefault('k', len(predicted_rank_vector))
        ndgc, err = segment.ndgc_err(predicted_rank_vector, original_rank_vector, k)
        ndgc_list.append(ndgc)
        err_list.append(err)
    avg_ndgc = average(ndgc_list)
    avg_err = average(err_list)
    return {'ndgc':avg_ndgc, 'err':avg_err}


def allmetrics(predicted_rank_vectors, original_rank_vectors,  **kwargs):
    stats = {}
    functions = [kendall_tau_set, mrr, best_predicted_vs_human, avg_predicted_ranked, avg_ndgc_err]
    for function in functions:
        stats.update(function(predicted_rank_vectors, original_rank_vectors, **kwargs))
    
    return stats

#if __name__ == '__main__':
#    from sentence.ranking import Ranking
#    a = Ranking([1,2,3,4])
#    b = Ranking([2,3,1,4])
#    
#    c = [a,b,a,b,a,a]
#    d = [b,a,a,b,a,]
#    
#    print avg_ndgc_err(c,d)
    
    