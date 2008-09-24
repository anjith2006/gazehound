# Part of the gazehound package for analzying eyetracking data
#
# Copyright (c) 2008 Board of Regents of the University of Wisconsin System
#
# Written by Nathan Vack <njvack@wisc.edu> at the Waisman Laborotory
# for Brain Imaging and Behavior, University of Wisconsin - Madison.
import csv
import re
from gazepoint import *

class DelimitedReader(object):
    
    """
    Converts files (or other enumerations of strings) into lists of lists.
    Optionally skips leading lines starting with some comment character
    (by defult the #)
    """

    STANDARD_DIALECT = {
        'delimiter': "\t"
    }
    def __init__(self, 
        file_data = None, skip_comments = True, comment_char = "#",
        opts_for_parser = {}
    ):
        self.__lines_cleaned = None
        self.parser = None
        self.file_data = file_data
        self.skip_comments = skip_comments
        self.comment_char = comment_char
        self.opts_for_parser = opts_for_parser
        for prop, val in self.__class__.STANDARD_DIALECT.iteritems():
            if not self.opts_for_parser.has_key(prop):
                self.opts_for_parser[prop] = val
    
    
    def __len__(self):
        self.__setup_parser()
        return len(self.__lines_cleaned)
    
    def comment_lines(self):
        comment_lines = []
        for line in self.file_data:
            stripped = line.strip()
            if (len(stripped) == 0 or
                stripped.startswith(self.comment_char)):
                comment_lines.append(line)
            else:
                break
        return comment_lines
    
    def __iter__(self):
        return self
    
    def next(self):
        self.__setup_parser()
        return self.parser.next()
        
    def __setup_parser(self):
        self.__set_lines_cleaned()
        if self.parser is None:
            self.parser = csv.reader(
                self.__lines_cleaned, **self.opts_for_parser
            )
        
    def __set_lines_cleaned(self):
        if self.__lines_cleaned is not None:
            return
            
        if not self.skip_comments:
            self.__lines_cleaned = self.file_data
            return
            
        for i in range(len(self.file_data)):
            stripped = self.file_data[i].strip()
            if (len(stripped) > 0 and not
                stripped.startswith(self.comment_char)):
                break
        
        self.__lines_cleaned = self.file_data[i:]
    

class IViewReader(DelimitedReader):

    # The second parameter is a function, taking one string argument,
    # that converts the value to its expected format.
    HEADER_MAP = {
        'FileVersion': ('file_version', str),
        'Fileformat': ('file_format', str),
        'Subject': ('subject', str),
        'Date': ('date_string', str),
        'Description': ('description', str),
        '# of Pts Recorded': ('recorded_points', int),
        'Offset Of Calibration Area': (
            'calibration_offset', lambda x: [int(e) for e in x.split("\t")]
        ),
        'Size Of Calibration Area': (
            'calibration_size', lambda x: [int(e) for e in x.split("\t")]
        ),
        'Sample Rate': ('sample_rate', int)
    }
    
    SEP = ":\t"
    
    """A reader for files produced by SMI's iView software"""
    def __init__(self, 
        file_data = None, skip_comments = True, comment_char = "#",
        opts_for_parser = {}):
        
        super(IViewReader, self).__init__(
            file_data, skip_comments, comment_char, opts_for_parser
        )
    
    def header(self):
        coms = self.comment_lines()
        coms = [re.sub('^#', '', l) for l in coms] # Strip leading "#"
        header_pairs = [l.split(self.__class__.SEP, 1) for l in coms]
        
        header_pairs = [p for p in header_pairs if len(p) == 2]
        # Kill line endings in header_pairs
        header_pairs = [[p[0], p[1].strip()] for p in header_pairs]
        
        header_ret = {}
        for p in header_pairs:
            cleaned_pair = self.__map_header_value(p)
            if cleaned_pair is not None:
                header_ret.update([cleaned_pair])
        return header_ret
        
    
    def scanpath(self):
        """Return a list of Points representing the scan path."""
        fact = IViewPointFactory()
        points = fact.from_component_list(self)
        return ScanPath(points = points)
    
    def __map_header_value(self, pair):
        """
        Return a tuple of the form (key, value), or None if 
        pair[0] isn't in HEADER_MAP
        """
        
        raw_key, raw_val = pair
        mapper = self.__class__.HEADER_MAP.get(raw_key)
        if mapper is None:
            return None
    
        cleaned_key, converter = mapper
        
        cleaned_val = converter(raw_val)
        return (cleaned_key, cleaned_val)
    
    