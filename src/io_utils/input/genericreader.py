'''
Created on Aug 4, 2011

@author: elav01
'''


from sentence.dataset import DataSet


class GenericReader:
    '''
    Abstract base class to describe the basic functionality of a reader, i.e. a mechanism that can
    import data from external entities (e.g. files) for use with the framework.
    '''
    
    
    def __init__(self, input_filename, load = True):
        """
        Constructor. Creates a memory object that handles file data
        @param input_filename: the name of file
        @type input_filename: string
        @param load: by turning this option to false, the instance will be 
                     initialized without loading everything into memory. This can be
                     done later by calling .load() function
        @type load: boolean 
        """
        self.input_filename = input_filename
        self.loaded = load
        if load:
            self.load()
    

    
    def load(self):
        raise NotImplementedError( "Should have implemented this" )

        
    def unload(self):
        raise NotImplementedError( "Should have implemented this" )

    
    def get_parallelsentence(self, XMLEntry):   
        raise NotImplementedError( "Should have implemented this" )

    def get_dataset(self):
        """
        Returns the contents of the parsed file into an object structure, which is represented by the DataSet object
        Note that this will cause all the data of the file to be loaded into system memory at once. 
        For big data sets this may not be optimal, so consider sentence-by-sentence reading with SAX, or CElementTree (e.g. saxjcml.py)
        @return the formed data set
        @rtype DataSet
        """
        return DataSet(self.get_parallelsentences())
        
    def get_parallelsentences(self):
        """
        Returns the contents of the parsed file into an a list with 
        ParallelSentence objects. Note that this will cause all the data of the file to be loaded into system memory at once. 
        For big data sets this may not be optimal, so consider sentence-by-sentence reading with SAX or CElementTree (e.g. saxjcml.py)
        @return the list of parallel sentences
        @rtype [ParallelSentence, ...]
        """
        raise NotImplementedError( "Should have implemented this" )

    
    
   

        