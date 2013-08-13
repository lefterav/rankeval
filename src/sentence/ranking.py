'''
Utility functions and classes for ranking. 
Can be used both in a pythonic or an object-oriented way wrapped in Ranking class

Created on 20 Mar 2013
@author: Eleftherios Avramidis
'''

def indexes(ranking_list, neededrank):
    '''
    Returns the indexes of the particular ranks in the list
    @param ranking_list: the list of ranks that will be searched
    @type ranking_list: list
    @param rank: a rank value
    @type rank: float
    @return: the indexes where the given rank appears
    @rtype: [int, ...]
    '''
    indexes = [index for index, rank in enumerate(ranking_list) if neededrank==rank]
    return indexes    

def _handle_tie(ranking_list, original_rank, modified_rank, ties_handling):
    ''' Modifies the values of the tied items as specified by the parameters
    @param ranking_list: the list of ranks
    @type ranking_list: list
    @param original_rank: the original rank value
    @type original_rank: float
    @param modified_rank: the new normalized rank value that would have been assigned if there was no tie 
    @type modified_rank: float
    @param ties_handling: A string defining the mode of handling ties. For the description see function normalized()
    @type: string
    @return: the new value of the given rank after considering its ties and the value of the rank that the normalization iteration should continue with
    @rtype: tuple(float, float)
    ''' 
    count = ranking_list.count(original_rank)
    if count <= 1:
        return modified_rank, modified_rank
    if ties_handling == 'minimize':
        return modified_rank, modified_rank
    if ties_handling == 'floor':
        return modified_rank, modified_rank+count-1
    if ties_handling == 'ceiling':
        return modified_rank+count-1, modified_rank+count-1
    if ties_handling == 'middle':
        return modified_rank-1 + (count+1.00)/2, modified_rank+count-1
    return modified_rank, modified_rank

def normalize(ranking_list, **kwargs):
    '''
    Convert a messy ranking like [1,3,5,4] to [1,2,4,3]
    @param ranking_list: the list of ranks that will be normalized
    @type ranking_list: list
    @keyword ties: Select how to handle ties. Accepted values are:
     - 'minimize', which reserves only one rank position for all tied items of the same rank
     - 'floor', which reserves all rank positions for all tied items of the same rank, but sets their value to the minimum tied rank position 
     - 'ceiling', which reserves all rank positions for all tied items of the same rank, but sets their value to the maximum tied rank position
     - 'middle', which reserves all rank positions for all tied items of the same rank, but sets their value to the middle of the tied rank positions
    @type inflate_ties: string 
    @return: a new normalized list of ranks
    @rtype: [float, ...]
    '''
    ties_handling = kwargs.setdefault('ties', 'minimize')
    
    length = len(ranking_list)
    
    #create an empty ranking list
    normalized_rank = [0]*length
    new_rank = 0
    #iterate through the ordered rank values in the list
    for original_rank in sorted(set(ranking_list)):
        #this is incrementing the actual order of the rank
        new_rank += 1
        #find the positions where this particular rank value appears
        rank_indexes = indexes(ranking_list, original_rank)
        #check if this particular rank value is tied and get the new rank value according to the tie handling preferences
        new_rank, next_rank = _handle_tie(ranking_list, original_rank, new_rank, ties_handling)
        #assign the new rank value to the respective position of the new ranking list
        for rank_index in rank_indexes:
            normalized_rank[rank_index] = new_rank
        #this is needed, if ties existed and the next rank needs to increment in a special way according to the tie handling preferences
        new_rank = next_rank
    #make sure that all ranks have been processed
    assert(normalized_rank.count(0)==0)
    return normalized_rank
            
def invert(ranking_list, **kwargs):
    '''
    Inverts a ranking list so that the best item becomes worse and vice versa
    @param ranking_list: the list whose ranks are to be inverted
    @type ranking_list: [float, ...]
    @return: the inverted rank list
    @rtype: [float, ...]
    '''
    inverted_ranking_list = [-1.0*item for item in ranking_list]
    return normalize(inverted_ranking_list, kwargs)
            
class Ranking(list):
    '''
    Class that wraps the functionality of a ranking list. It behaves as normal list but also allows additional functions to be performed, that are relevant to ranking
    @ivar list: the ranking
    @rtype list: [float, ...]
    @ivar normalization: describes what kind of normalization has been been performed to the internal list
    @rtype normalization: string
    '''

    def __init__(self, ranking, **kwargs):
        '''
        @param ranking: a list of values representing a ranking
        @type ranking: list of floats, integers or strings
        '''
        #convert to float, in order to support intermediate positions
        
        integers = kwargs.setdefault('integers', False)
        
        for i in ranking:
            if not integers:
                self.append(float(i))
            else: 
                self.append(int(round(float(i),0)))
        self.normalization = kwargs.setdefault('normalization', 'unknown')
        
    def __setitem__(self, key, value):
        self.normalization = 'unknown'
        super(Ranking, self).__setitem__(key, float(value))
        
        
    def __delitem__(self, key):
        self.normalization = 'unknown'
        super(Ranking, self).__delitem__(key)
        
    
    def normalize(self, **kwargs):
        '''
        Create a new normaliyed ranking out of a messy ranking like [1,3,5,4] to [1,2,4,3]
        @keyword ties: Select how to handle ties. Accepted values are:
         - 'minimize', which reserves only one rank position for all tied items of the same rank
         - 'floor', which reserves all rank positions for all tied items of the same rank, but sets their value to the minimum tied rank position 
         - 'ceiling', which reserves all rank positions for all tied items of the same rank, but sets their value to the maximum tied rank position
         - 'middle', which reserves all rank positions for all tied items of the same rank, but sets their value to the middle of the tied rank positions
        @type inflate_ties: boolean 
        @return a new normalized ranking
        @rtype Ranking 
        '''
        ties_handling = kwargs.setdefault('ties', 'minimize')
        return Ranking(normalize(self, ties=ties_handling), normalization=ties_handling)
    
    def indexes(self, neededrank):
        '''
        Returns the indexes of the particular ranks in the list
        @param ranking_list: the list of ranks that will be searched
        @type ranking_list: list
        @param rank: a rank value
        @type rank: float
        @return: the indexes where the given rank appears
        @rtype: [int, ...]
        '''
        return indexes(self, neededrank)   

    def inverse(self, **kwargs):
        '''
        Created an inverted ranking, so that the best item becomes worse
        @keyword ties: Select how to handle ties. Accepted values are:
         - 'minimize', which reserves only one rank position for all tied items of the same rank
         - 'floor', which reserves all rank positions for all tied items of the same rank, but sets their value to the minimum tied rank position 
         - 'ceiling', which reserves all rank positions for all tied items of the same rank, but sets their value to the maximum tied rank position
         - 'middle', which reserves all rank positions for all tied items of the same rank, but sets their value to the middle of the tied rank positions
        @return: the inverted ranking
        @rtype: Ranking
        '''
        ties_handling = kwargs.setdefault('ties', 'minimize')
        return Ranking(invert(self, ties=ties_handling), normalization=ties_handling)

    def integers(self):
        '''
        Return a version of the ranking, only with integers. It would be nice if the Ranking is normalized
        @return: a new ranking with integers
        @rtype: Ranking
        ''' 
        
        return Ranking(self, integers=True)
            


#    
#if __name__ == '__main__':
#    r = Ranking([1,2,3,2.2,4])
#    r[0] = '0'
##    
#    print r.normalize(ties='ceiling').integers()
##    
#    
#            
            
            
            
            
            
            
        
    
    

        
        