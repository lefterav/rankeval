#!/usr/bin/python
# -*- coding: utf-8 -*-

"""

@author: Eleftherios Avramidis
"""

import sys
import re
from compiler.ast import Raise

class DataSet(object):
    """
    A wrapper over a list of parallelsentences. It offers convenience functions for features and properties that 
    apply to the entire set of parallelsentences altogether
    @ivar parallelsentences: a list of the contained parallel sentence instances
    @type parallelsentences: [L{ParallelSentence}, ...]  
    @ivar attribute_names: (optional) keeps track of the attributes that can be found in the contained parallel sentences
    @type attribute_names: [str, ...]
    @ivar attribute_names_found: remembers if the attribute names have been set
    @type attribute_names_found: boolean
    """

    def __init__(self, content = [], attributes_list = [], annotations = []):
        """
        @param parallelsentence_list: the parallelsentences to be wrapped in the dataset
        @type parallelsentence_list: [L{ParallelSentence}, ...]
        @param attributes_list: if the names of the attributes for the parallelsentences are known, they can 
        be given here, in order to avoid extra processing. Otherwise they will be computed when needed.
        @type [str, ...]
        @param annotations: Not implemented
        @type list     
        """
        
        if isinstance(content, DataSet) or issubclass(content.__class__, DataSet):
            self.parallelsentences = content.parallelsentences
            self.annotations = content.annotations
            self.attribute_names = content.attribute_names
            self.attribute_names_found = content.attribute_names_found
        
        else:
            
            self.parallelsentences = content
            self.annotations = annotations    
            if attributes_list:
                self.attribute_names = attributes_list
                self.attribute_names_found = True
            else:
                self.attribute_names_found = False
                self.attribute_names = []
            self.ensure_judgment_ids()
                
    def ensure_judgment_ids(self):
        """
        Processes one by one the contained parallel sentences and ensures that there are judgment ids
        otherwise adds an incremental value
        """
        i = 0
        try:
            for parallelsentence in self.parallelsentences:
                i += 1
                if not parallelsentence.has_judgment_id():
                    parallelsentence.add_judgment_id(i)
        except:
            pass

    
    def get_parallelsentences(self):
        return self.parallelsentences
    
    
    def get_parallelsentences_per_sentence_id(self):
        """
        Group the contained parallel sentences by sentence id 
        @return: a dictionary with lists of parallel sentences for each sentence id
        @rtype: dict(String, list(sentence.parallelsentence.ParallelSentence))
        """
        ps_sid = {}
        for parallelsentence in self.parallelsentences:
            #get the id of the particular multiple ranking (judgment) or create a new one
            sentence_id = parallelsentence.get_compact_id()
            if not ps_sid.has_key(sentence_id):
                ps_sid[sentence_id] = [parallelsentence]
            else:
                ps_sid[sentence_id].append(parallelsentence)
        return ps_sid        
                
    
    def get_parallelsentences_with_judgment_ids(self):
        """
        Parallel sentences often come with multiple occurences, where a judgment id is unique.
        This functions returns a dictionary of all the parallel sentences mapped to their respective judgment id.
        If a judment id is missing, it gets assigned the incremental value showing the order of the entry in the set.
        @return: A dictionary of all the parallel sentences mapped to their respective judgment id.
        @rtype: dict
        """
        ps_jid = {}
        j = 0
        for parallelsentence in self.parallelsentences:
            #get the id of the particular multiple ranking (judgment) or create a new one
            try:
                judgement_id = parallelsentence.get_attribute("judgment_id")
            except AttributeError:
                judgement_id = str(j)
            j += 1
            
            #add the pair into the dictionary
            ps_jid[judgement_id] = parallelsentence
        return ps_jid
    
    
    def get_annotations(self):
        return self.annotations
    
    def get_attribute_names(self):
        if not self.attribute_names_found: 
            self.attribute_names = self._retrieve_attribute_names()
            self.attribute_names_found = True
        return self.attribute_names
    
    def get_all_attribute_names(self):
        all_attribute_names =  self.get_attribute_names()
        all_attribute_names.extend( self.get_nested_attribute_names() )
        return list(set(all_attribute_names))
    
    def get_nested_attribute_names(self):
        nested_attribute_names = set()
        for parallelsentence in self.parallelsentences:
            nested_attribute_names.update ( parallelsentence.get_nested_attributes().keys() )
        return list(nested_attribute_names)
    
    def _retrieve_attribute_names(self):
        attribute_names = set()
        for parallelsentence in self.parallelsentences:
            attribute_names.update( parallelsentence.get_attribute_names() )
        return list(attribute_names)

    def get_discrete_attribute_values(self, discrete_attribute_names):
        attvalues = {}
        for parallelsentence in self.parallelsentences:
            allattributes = {}
            allattributes.update(parallelsentence.get_nested_attributes())
            allattributes.update(parallelsentence.attributes)
            for attname in discrete_attribute_names:
                if attname in allattributes:
                    attvalue = allattributes[attname]
                    try:
                        attvalues[attname].add(attvalue)
                    except:
                        attvalues[attname] = set([attvalue])
        return attvalues

    def confirm_attributes(self, desired_attributes=[], meta_attributes=[]):
        """
        Convenience function that checks whether the user-requested attributes (possibly
        via the config file) exist in the current dataset's list. If not, raise an error
        to warn him of a possible typo or so.
        @param desired_attributes: attributes that need to participate in the ML process
        @rtype desired_attributes: [str, ...]
        @param meta_attributes: attributes that need not participate in the ML process (meta)
        @rtype meta_attributes: [str, ...]
        """
        attribute_names = self.get_all_attribute_names()
        asked_attributes = set(desired_attributes.extend(meta_attributes))
        for asked_attribute in asked_attributes:
            if asked_attribute not in attribute_names:
                sys.stderr.write("Requested feature %s probably not available\n" % asked_attribute)
                raise KeyError 
    
    def append_dataset(self, add_dataset):
        """
        Appends a given data set to the end of the current dataset in place
        @param add_dataset: dataset to be appended
        @rtype add_dataset: L{DataSet}
        """
        self.parallelsentences.extend(add_dataset.get_parallelsentences())
        existing_attribute_names = set(self.get_attribute_names())
        new_attribute_names = set(add_dataset.get_attribute_names())
        merged_attribute_names = existing_attribute_names.union(new_attribute_names)
        self.attribute_names = list(merged_attribute_names)
    
    #attribute_replacements = {"rank": "predicted_rank"}
    def merge_dataset(self, dataset_for_merging_with, attribute_replacements = {}, merging_attributes = ["id"], merge_strict = False, **kwargs):
        """
        It takes a dataset which contains the same parallelsentences, but with different attributes.
        Incoming parallel sentences are matched with the existing parallel sentences based on the "merging attribute". 
        Incoming attributes can be renamed, so that they don't replace existing attributes.
        @param dataset_for_merging_with: the data set whose contents are to be merged with the current data set
        @type dataset_for_merging_with: DataSet
        @param attribute_replacements: listing the attribute renamings that need to take place to the incoming attributes, before the are merged
        @type attribute_replacements: list of tuples
        @param merging_attributes: the names of the attributes that signify that two parallelsentences are the same, though with possibly different attributes
        @type merging_attributes: list of strings  
        """
        incoming_parallelsentences_indexed = {}        
        incoming_parallelsentences = dataset_for_merging_with.get_parallelsentences()
        for incoming_ps in incoming_parallelsentences:
            key = tuple([incoming_ps.get_attribute(att) for att in merging_attributes]) #hopefully this runs always in the same order
            incoming_parallelsentences_indexed[key] = incoming_ps
            
        
        for i in range(len(self.parallelsentences)):
            if self.parallelsentences[i]:
                key = tuple([self.parallelsentences[i].get_attribute(att) for att in merging_attributes]) #hopefully this runs always in the same order
            try:
                incoming_ps = incoming_parallelsentences_indexed[key]
                self.parallelsentences[i].merge_parallelsentence(incoming_ps, attribute_replacements, **kwargs)
            except:
                sys.stderr.write( "Didn't find key while merging sentence %s " % key )
                if merge_strict:
                    self.parallelsentences[i] = None
                pass
            
    
    #attribute_replacements = {"rank": "predicted_rank"}
    def merge_dataset_symmetrical(self, dataset_for_merging_with, attribute_replacements = {}, confirm_attribute = ""):
        """
        Merge the current dataset in place with another symmetrical dataset of the same size and the same original content, but
        possibly with different attributes per parallel sentence
        @param dataset_for_merging_with: the symmetrical dataset with the same order of parallel sentences
        @type dataset_for_merging_with: L{DataSet}
        @param attribute_replacements: a dict of attribute replacements that need to take place, before merging occurs
        @type attribute_replacements: {str, str; ...}
        """
        incoming_parallelsentences = dataset_for_merging_with.get_parallelsentences()
        if len(self.parallelsentences) != len(incoming_parallelsentences):
            raise IndexError("Error, datasets not symmetrical")
        if confirm_attribute != "":
            vector1 = [ps.get_attribute(confirm_attribute) for ps in self.get_parallelsentences()]
            vector2 = [ps.get_attribute(confirm_attribute) for ps in dataset_for_merging_with.get_parallelsentences()]
            if vector1 != vector2:
                raise IndexError("Error, datasets not symmetrical, concerning the identifier attribute {}".format(confirm_attribute))
    
        for i in range(len(self.parallelsentences)):
            incoming_ps = incoming_parallelsentences[i]
            self.parallelsentences[i].merge_parallelsentence(incoming_ps, attribute_replacements)
            
    
    def merge_references_symmetrical(self, dataset_for_merging_with):
        incoming_parallelsentences = dataset_for_merging_with.get_parallelsentences()
        if len(self.parallelsentences) != len(incoming_parallelsentences):
            raise IndexError("Error, datasets not symmetrical")
        for i in range(len(self.parallelsentences)):
            self.parallelsentences[i].ref = incoming_parallelsentences[i].ref
    
               
    def get_translations_count_vector(self):
        return [len(ps.get_translations()) for ps in self.get_parallelsentences()]
    
    
    def get_singlesource_strings(self):
        return [ps.get_source().get_string() for ps in self.parallelsentences]
    
    
    def write_singlesource_strings_file(self, filename = None):
        import tempfile
        if not filename:
            file = tempfile.mkstemp(text=True)
            filename = file.name
        else:
            file = open(filename, 'w')
        for source in self.get_singlesource_strings():
            file.write(source)
            file.write('\n')
        file.close()
        return filename 
    
    def get_multisource_strings(self):
        raise NotImplementedError
    
    def get_target_strings(self):
        output = []
        for ps in self.parallelsentences:
            output.append([tgt.get_string() for tgt in ps.get_translations()])
        return output
            
    def modify_singlesource_strings(self, strings = []):
        for string, ps in zip(strings, self.parallelsentences):
            ps.src.string = string
    
    def modify_target_strings(self, strings = []):
        for stringlist, ps in zip(strings, self.parallelsentences):
            for string, tgt in zip(stringlist, ps.tgt):
                tgt.string = string
                   
        
         
            
    
    def remove_ties(self):
        """
        Modifies the current dataset by removing ranking ties        
        """
        for ps in self.parallelsentences:
            ps.remove_ties()
            
   
    def get_size(self):
        return len(self.parallelsentences)
    
    def get_head_sentences(self, n):
        return self.parallelsentences[:n]
    
    def get_tail_sentences(self, n):
        return self.parallelsentences[-1 * n:]
    
    def split(self, ratio):
        size = int(round(ratio * len(self.parallelsentences)))
        return DataSet(self.parallelsentences[:size-2]), DataSet(self.parallelsentences[size-1:]) 
    
    def add_attribute_vector(self, att_vector, target="tgt", item=0):
        att_vector.reverse()
        
        for ps in self.parallelsentences:
            atts = att_vector.pop()
            atts = dict([(k, str(v)) for k,v in atts.iteritems()])
            if target == "ps":
                ps.add_attributes(atts)
            elif target == "tgt":
                ps.tgt[item].add_attributes(atts)
            elif target == "src":
                ps.src.add_attributes(atts)
    
    
    def select_attribute_names(self, expressions=[]):
        attribute_names = set()
        #compile the list of expressions first, so that there is minimal overhead
        compiled_expressions = [re.compile(expression) for expression in expressions]
        for expression in compiled_expressions:
            for attribute_name in self.get_all_attribute_names(): 
                if re.match(expression, attribute_name):
                    attribute_names.add(attribute_name)
                else:
                    print "tzifos"
        return list(attribute_names)
            
    
    def clone(self):
        return DataSet(self.parallelsentence, self.attribute_names)
    
    """
     def get_nested_attributes(self):

        propagated_parallelsentences = []
        propagated_attribute_names = set()
        for psentence in self.parallelsentences:
            psentence.propagate_attributes()
            propagated_parallelsentences.append(psentence)
            propagated_attribute_names.add( psentence.get_attributes() )
        self.parallelsentences = propagated_parallelsentences
        self.attribute_names = list( propagated_attribute_names )
    """
    
    def __eq__(self, other):
        """
        @todo comparison doesn't really work
        """
        i = 0
        for ps_here, ps_other in zip(self.parallelsentences, other.parallelsentences):
            i+=1
            if not ps_here == ps_other:
                print "Sentence %d with id %s-%s seems to be unequal"% (i, ps_here.get_attribute("ps1_id"), ps_here.get_attribute("ps2_id"))
                return False
        return True
#        return self.parallelsentences == other.parallelsentences
    
    def compare(self, other_dataset, start=0, to=None ):
        """
        Compares this dataset to another, by displaying parallel sentences in pairs
        """
        if not to:
            to = len(self.parallelsentences)-1
        for ps1 in self.parallelsentences[start:to]:
            for ps2 in other_dataset.get_parallelsentences():
                if ps2.get_attributes()["id"] == ps1.get_attributes()["id"] and ps2.get_attributes()["testset"] == ps1.get_attributes()["testset"] and ps2.get_attributes()["langsrc"] == ps1.get_attributes()["langsrc"]:
                    print ps1.get_source().get_string() , "\n",  ps2.get_source().get_string()
                    print ps1.get_attributes() , "\n", ps2.get_attributes()
                    print ps1.get_translations()[0].get_string() , "\n",  ps2.get_translations()[0].get_string()
                    print ps1.get_translations()[0].get_attributes() , "\n",  ps2.get_translations()[0].get_attributes()
                    print ps1.get_translations()[1].get_string() , "\n",  ps2.get_translations()[1].get_string()
                    print ps1.get_translations()[1].get_attributes() , "\n",  ps2.get_translations()[1].get_attributes()
            


    def __iter__(self):
        """
        A DataSet iterates over its basic wrapped object, ParallelSentence
        """
        return self.parallelsentences.__iter__()
