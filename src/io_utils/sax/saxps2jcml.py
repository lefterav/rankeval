'''
Created on 14 Dec 2011

@author: Eleftherios Avramidis
'''

import shutil
import sys
import os
import re
import tempfile
from random import shuffle
from xml.sax.saxutils import XMLGenerator
from xml.sax.xmlreader import AttributesImpl
from io_utils.dataformat.jcmlformat import JcmlFormat
from sentence.sentence import SimpleSentence
from sentence.dataset import DataSet


#compile the much needed regular expression
illegal_xml_chars_RE = re.compile(u'[\x00-\x08\x0b\x0c\x0e-\x1F\uD800-\uDFFF\uFFFE\uFFFF]') 


def c(string):
    """
    Kills extended unicode characters that are not allowed in a proper XML 
    """     
    clean_string, rep = illegal_xml_chars_RE.subn('', string)
    if rep > 0:
        sys.stderr.write("I had to kill {0} unicode characters because they were not XML-compliant\n".format(rep))
    
    return clean_string.strip()



class IncrementalJcml(object):
    """
    Write line by line incrementally on an XML file, without loading anything in the memory.
    Don't forget the close function. Object sentences cannot be edited after written
    """
    def __init__(self, filename, xmlformat=JcmlFormat):
        self.TAG = xmlformat.TAG
        self.filename = filename
        self.file = tempfile.NamedTemporaryFile(mode='w',delete=False,suffix='.jcml', prefix='tmp_', dir='.') #"/tmp/%s.tmp" % os.path.basename(filename)
        self.tempfilename = self.file.name
#        self.file = open(self.tempfilename, 'w')
        self.generator = XMLGenerator(self.file, "utf-8")
        self.generator.startDocument()
        self.generator.startElement(self.TAG["doc"], {})
        
    def add_parallelsentence(self, parallelsentence):
        self.generator.characters("\n\t")
        #convert all attribute values to string, otherwise it breaks
        attributes = dict([(key,str(val)) for key,val in parallelsentence.get_attributes().iteritems()])
        self.generator.startElement(self.TAG["sent"], attributes)
        
        src = parallelsentence.get_source()
        
        if isinstance(src, SimpleSentence):            
                                
            self.generator._write("\n\t\t")
            src_attributes = dict([(key,str(val)) for key,val in src.get_attributes().iteritems()])
            self.generator.startElement(self.TAG["src"], src_attributes)
            self.generator.characters(c(src.get_string()))
            self.generator.endElement(self.TAG["src"])
        elif isinstance(src, tuple):
            for src in parallelsentence.get_source():
                self.generator._write("\n\t\t")
                src_attributes = dict([(key,str(val)) for key,val in src.get_attributes().iteritems()])
                self.generator.startElement(self.TAG["src"], src_attributes)
                self.generator.characters(c(src.get_string()))
                self.generator.endElement(self.TAG["src"])
        
        for tgt in parallelsentence.get_translations():
            self.generator._write("\n\t\t")
            tgt_attributes = dict([(key,str(val)) for key,val in tgt.get_attributes().iteritems()])
            self.generator.startElement(self.TAG["tgt"], tgt_attributes)
            self.generator.characters(c(tgt.get_string()))
            self.generator.endElement(self.TAG["tgt"])
        
        
        ref = parallelsentence.get_reference()
        if ref and ref.get_string() != "":
            self.generator._write("\n\t\t")
            ref_attributes = dict([(key,str(val)) for key,val in ref.get_attributes().iteritems()])
            self.generator.startElement(self.TAG["ref"], ref_attributes)
            self.generator.characters(c(ref.get_string()))
            self.generator.endElement(self.TAG["ref"])
        
        self.generator._write("\n\t")
        self.generator.endElement(self.TAG["sent"])
        
    
    def close(self):
        self.generator.characters("\n")
        self.generator.endElement(self.TAG["doc"])
        self.generator.characters("\n")
        self.generator.endDocument()
        self.file.close()
        shutil.move(self.tempfilename, self.filename)
        

class Parallelsentence2Jcml(object):
    '''
    This is a helper class which is meant to produce quickly an XML file
    given a list of parallel sentences, without loading a new heavy XML object 
    into the memory
    '''

    def __init__(self, parallelsentences, format = JcmlFormat(), **kwargs):
        '''
        Provide a list of parallel sentences
        '''
        
        self.shuffle_translations = kwargs.setdefault("shuffle_translations", False)
        self.sort_attribute = kwargs.setdefault("sort_attribute", None)
                    
        if isinstance (parallelsentences, DataSet):
            self.parallelsentences = parallelsentences.get_parallelsentences()
        else:
            self.parallelsentences = parallelsentences
        
        self.TAG = format.TAG
    
        
    def write_to_file(self, filename):
        '''
        XML output is written to the desired file
        '''
        tempfilename = "%s.tmp" % filename 
        f = open(tempfilename, 'w')
        generator = XMLGenerator(f, "utf-8")
        generator.startDocument()
        generator.startElement(self.TAG["doc"], {})

        for parallelsentence in self.parallelsentences:
            generator.characters("\n\t")
            attributes = dict([(k,str(v)) for k,v in parallelsentence.get_attributes().iteritems()])
            generator.startElement(self.TAG["sent"], attributes)
            
            src = parallelsentence.get_source()
            attributes = dict([(k,str(v)) for k,v in src.get_attributes().iteritems()])
            
            if isinstance(src, SimpleSentence):            
                                    
                generator._write("\n\t\t")
                generator.startElement(self.TAG["src"], attributes)
                generator.characters(c(src.get_string()))
                generator.endElement(self.TAG["src"])
            elif isinstance(src, tuple):
                for src in parallelsentence.get_source():
                    generator._write("\n\t\t")
                    generator.startElement(self.TAG["src"], attributes)
                    generator.characters(c(src.get_string()))
                    generator.endElement(self.TAG["src"])
            
            translations = parallelsentence.get_translations()
            
            if self.shuffle_translations:
                shuffle(translations)
            

            
            if self.sort_attribute:
                translations = sorted(translations, key=lambda tgt: tgt.get_attribute(self.sort_attribute))
            
            
            for tgt in translations:
                generator._write("\n\t\t")
                attributes = dict([(k,str(v)) for k,v in tgt.get_attributes().iteritems()])
                generator.startElement(self.TAG["tgt"], attributes)
                generator.characters(c(tgt.get_string()))
                generator.endElement(self.TAG["tgt"])
            
            
            ref = parallelsentence.get_reference()
            if ref and ref.get_string() != "":
                generator._write("\n\t\t")
                attributes = dict([(k,str(v)) for k,v in ref.get_attributes().iteritems()])
                generator.startElement(self.TAG["ref"], attributes)
                generator.characters(c(ref.get_string()))
                generator.endElement(self.TAG["ref"])
            
            generator._write("\n\t")

            
            
            generator.endElement(self.TAG["sent"])
        generator.characters("\n")
        generator.endElement(self.TAG["doc"])
        generator.characters("\n")
        generator.endDocument()
        f.close()
        shutil.move(tempfilename, filename)
            
            