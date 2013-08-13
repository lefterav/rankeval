#!/usr/bin/python
# -*- coding: utf-8 -*-


"""
Created on 15 Οκτ 2010

@author: Eleftherios Avramidis
"""


import re
import math
import os
from xml.dom import minidom
from sentence.parallelsentence import ParallelSentence
from sentence.sentence import SimpleSentence
from xml.sax.saxutils import unescape
from io_utils.input.genericreader import GenericReader
from io_utils.sax.saxps2jcml import Parallelsentence2Jcml

class GenericXmlReader(GenericReader):
    """
    classdocs
    """

    
    def __init__(self, input_filename, load = True, stringmode = False):
        """
        Constructor. Creates an XML object that handles ranking file data
        @param input_filename: the name of XML file
        @type input_filename: string
        @param load: by turning this option to false, the instance will be 
                     initialized without loading everything into memory
        @type load: boolean 
        """
        
        self.input_filename = input_filename
        self.loaded = load
        self.TAG = self.get_tags()
        if load:
            if stringmode:
                self.load_str(input_filename)
            else:
                self.load()
            
            
    def get_tags(self):
        return {}
 
    
    def load_str(self, input):
        self.xmlObject = minidom.parseString(input)
    
    
    def load(self):
        """
        Loads the data of the file into memory. It is useful if the Classes has been asked not to load the filename upon initialization
        """
        self.xmlObject = minidom.parse(self.input_filename)
    
    
#    def get_dataset(self):
#        """
#        Returs the contents of the XML file into an object structure, which is represented by the DataSet object
#        Note that this will cause all the data of the XML file to be loaded into system memory at once. 
#        For big data sets this may not be optimal, so consider sentence-by-sentence reading with SAX (saxjcml.py)
#        @rtype: sentence.dataset.DataSet
#        @return: A data set containing all the data of the XML file
#        """
#        #return DataSet(self.get_parallelsentences(), self.get_attributes(), self.get_annotations())
#        return DataSet(self.get_parallelsentences())
    
    
#    def get_annotations(self):
#        """
#        @return a list with the names of the annotation layers that the corpus has undergone
#        """
#        try:
#            annotations_xml_container = self.xmlObject.getElementsByTagName(self.TAG["annotations"])
#            annotations_xml = annotations_xml_container[0].getElementsByTagName(self.TAG_ANNOTATION)
#            return [annotation_xml["name"] for annotation_xml in annotations_xml]
#        except:
#            print "File doesn't contain annotation information"
#            return []
#        
    
    
    def split_and_write(self, parts, re_split):
        """
        Convenience function that splits an XML file into parts and writes them directly to the disk
        into .part files with similar filenames. The construction of the resulting filenames defined 
        by parameters 
        @param parts
        Number of parts to split into 
        @type int 
        @param re_split Regular expression which should define two (bracketed) groups upon the filename. 
        The resulting files will have the part number inserted in the filename between these two parts
        """
        parallelsentences = self.get_parallelsentences()
        inputfilename = os.path.basename(self.input_filename)
        length = len(parallelsentences)
        step = int(math.ceil(1.00 * len(parallelsentences) / parts)) #get ceiling to avoid mod
        partindex = 0 
        for index in range(0, length, step):
            partindex += 1
            start = index
            end = index + step
            print start, end
            try:
                print inputfilename
                filename_prefix, filename_suffix = re.findall(re_split, inputfilename)[0]
                filename = "%s.%2.d.part.%s" % (filename_prefix, partindex, filename_suffix)
                Parallelsentence2Jcml(parallelsentences[start:end]).write_to_file(filename)
            except IndexError:
                print "Please try to not have a dot in the test set name, cause you don't help me with splitting"

        
    
    
    def get_attributes(self):
        """
        @return a list of the names of the attributes contained in the XML file
        """
        judgedCorpus = self.xmlObject.getElementsByTagName(self.TAG["doc"])
        sentenceList = judgedCorpus[0].getElementsByTagName(self.TAG["sent"])
        attributesKeySet = set()
        
        for xml_entry in sentenceList:
            for attributeKey in xml_entry.attributes.keys():
                attributesKeySet.add(attributeKey)            
        return list(attributesKeySet)
    
    def length(self):
        judgedCorpus = self.xmlObject.getElementsByTagName(self.TAG["doc"])
        return len(judgedCorpus[0].getElementsByTagName(self.TAG["sent"]))
    
    
    def get_parallelsentence(self, xml_entry):
        
        srcXMLentries = xml_entry.getElementsByTagName(self.TAG["src"])
        tgtXMLentries = xml_entry.getElementsByTagName(self.TAG["tgt"])
        refXML = xml_entry.getElementsByTagName(self.TAG["ref"])
        
        if len(srcXMLentries) == 1 :
            src = self._read_simplesentence(srcXMLentries[0])
        elif len(srcXMLentries) > 1:
            src = [self._read_simplesentence(srcXML) for srcXML in srcXMLentries] 
            
        
        #Create a list of SimpleSentence objects out of the object
        tgt = [self._read_simplesentence(tgtXML) for tgtXML in tgtXMLentries] 
        
        ref = SimpleSentence()
        try:    
            ref = self._read_simplesentence(refXML[0])
        except LookupError:
            pass
        
        #Extract the XML features and attach them to the ParallelSentenceObject
        attributes = self._read_attributes(xml_entry)
        
        #TODO: fix this language by getting from other parts of the sentence
        if not self.TAG["langsrc"]  in attributes:
            attributes[self.TAG["langsrc"] ] = self.TAG["default_langsrc"] 
        
        if not self.TAG["langtgt"]  in attributes:
            attributes[self.TAG["langtgt"] ] = self.TAG["default_langtgt"] 
    
        
        #create a new Parallesentence with the given content
        curJudgedSentence = ParallelSentence(src, tgt, ref, attributes)
        return curJudgedSentence
        
    def get_parallelsentences(self, start = None, end = None):
        """
        @return: a list of ParallelSentence objects
        """
        judgedCorpus = self.xmlObject.getElementsByTagName(self.TAG["doc"])
        if not start and not end:
            sentenceList = judgedCorpus[0].getElementsByTagName(self.TAG["sent"])
        else:
            sentenceList = judgedCorpus[0].getElementsByTagName(self.TAG["sent"])[start:end]
        newssentences = [] 
        for xml_entry in sentenceList:
            curJudgedSentence = self.get_parallelsentence(xml_entry)
            newssentences.append(curJudgedSentence)
        return newssentences
    
    def _read_simplesentence(self, xml_entry):
        return SimpleSentence(self._read_string(xml_entry), self._read_attributes(xml_entry))
    
    def _read_string(self, xml_entry):
        try:
            return unescape(xml_entry.childNodes[0].nodeValue.strip()) #.encode('utf8')
        except:
            return ""

    
    def _read_attributes(self, xml_entry):
        """
        @return: a dictionary of the attributes of the current sentence {name:value}
        """
        attributes = {}
        attributeKeys = xml_entry.attributes.keys()
        for attributeKey in attributeKeys:
            myAttributeKey = attributeKey #.encode('utf8')
            attributes[myAttributeKey] = unescape(xml_entry.attributes[attributeKey].value) #.encode('utf8')                     
        return attributes
        
    