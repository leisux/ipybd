"""
Author: M Maher, Xu Zhoufeng
Date: 20171202

CSV/Excel->Pandas.DataFrame->Python Dict->Mustache-templated Html articles

then open .html file in browser; print

"""

#!/usr/bin/python

from ipybd.core import RestructureTable
import os
from ipybd.std_table_terms import HerbLabelTerms
import pandas as pd
from ipybd.label.herb_label import HerbLabel
import pystache


HERE = os.path.dirname(__file__)
CSS_PATH = os.path.join(HERE, 'label_format.css')

class Label(RestructureTable):
    columns_model = HerbLabelTerms
    def __init__(self, io, repeat=1):
        super(Label, self).__init__(io, fcol="")
        self._re_range_columns(cut=True)
        self.repeat = repeat
        self.outfile = os.path.splitext(io)[0] + '.html'

    def to_dict(self):
        records =  list(self.df.to_dict('record'))
        for i, record in enumerate(records):
            c = record.copy()
            for key, value in c.items():
                if not pd.Series(value).any():
                    record[key] = ""    
        return records

    def mustachify(self):
        """
        Converts a Dict object containing herbarium specimen records 
        into a list of Mustache-templated HTML articles.
        """
        records = self.to_dict()
        labels = []
        if self.repeat == 0:
            for l in records:
                try:
                    labels.extend([HerbLabel(l)]*l['individualCount'])
                    # if the field value not a valid number, default repeat = 1
                except:
                    labels.append(HerbLabel(l))
        elif isinstance(self.repeat, int):
            for l in records:
                labels.extend([HerbLabel(l)]*self.repeat)
            
        return labels
    
    def write_html(self):
        """
        Makes list of Mustache-templated HTML articles, then iterates over list 
        to generate complete HTML code containing all of the articles.
        """
        count = 0
        labels = self.mustachify()
        renderer = pystache.Renderer()
        with open(self.outfile, 'w') as fh:
            fh.write("<!DOCTYPE html><html><head><link rel=\"stylesheet\" href=\"" + CSS_PATH + "\"/></head><body>")
            fh.write("<div class=\"item-wrapper\">")
            for l in labels:
                count += 1
                labeltext = renderer.render(l)
                fh.write(labeltext)
                if count%6 == 0:
                    fh.write("</div><div class=\"item-wrapper\">")
            fh.write("</div></body></html>")


