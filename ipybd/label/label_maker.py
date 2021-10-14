"""
Author: Xu Zhoufeng, M Maher
Date: 20171202

CSV/Excel->Pandas.DataFrame->Python Dict->Mustache-templated Html articles

then open .html file in browser; print

"""

#!/usr/bin/python

import os
import re
import platform

import pandas as pd
import pystache
from ipybd.core import RestructureTable
from ipybd.label.herb_label import HerbLabel
from ipybd.std_table_terms import HerbLabelTerms
from pystrich.code128 import Code128Encoder

HERE = os.path.dirname(__file__)


class Label(RestructureTable):
    columns_model = HerbLabelTerms

    def __init__(self, io, repeat=1):
        """
        io: CSV/Excel file path
        repeat: A positive integer indicating the number of copies of
                the label to be printed, if it is zero, the number of
                copies is based on duplicatesOfLabel field.
        """
        super(Label, self).__init__(io, fields_mapping=True, cut=True, fcol="")
        self.repeat = repeat
        self.path = os.path.splitext(io)[0]
        self.outfile = os.path.join(self.path, 'Labels.html')

    def to_dict(self):
        records = list(self.df.to_dict(orient='records'))
        for i, record in enumerate(records):
            c = record.copy()
            for key, value in c.items():
                # null value fill ""
                if not pd.Series(value).any():
                    record[key] = ""
        return records

    def mustachify(self, start_code=None):
        """
        Converts a Dict object containing herbarium specimen records
        into a list of Mustache-templated HTML articles.

        add duplicate records in Dict object and DataFrame
        then save the DataFrame to excel file
        """
        records = self.to_dict()
        labels = []
        barcode_path = os.path.join(self.path, 'barcodes')
        try:
            # creat a new dir, Will be used to store code images
            os.mkdir(self.path)
            os.mkdir(barcode_path)
        except FileExistsError:
            pass
        if start_code:
            prefix, num, num_length = self.barcode_analyzer(start_code)
            # creat a new DataFrame, and add new record to this DataFrame
            # that with new code Number and new duplicate records
            new_table = pd.DataFrame()
        if self.repeat == 0:
            for r in records:
                try:
                    if start_code:
                        for _ in range(r['duplicatesOfLabel']):
                            code = self.code_maker(
                                prefix, str(num), num_length)
                            # add code image path to HerbLabel instance properties
                            # then the code image will be linked to the label
                            r['code_path'] = os.path.join(
                                barcode_path, code+".png")
                            labels.append(HerbLabel(r))
                            del r['code_path']
                            r['catalogNumber'] = code
                            new_table = new_table.append(r, ignore_index=True)
                            num += 1
                    else:
                        if r['catalogNumber'] != "" and r['duplicatesOfLabel'] == 1:
                            prefix, num, num_length = self.barcode_analyzer(r['catalogNumber'])
                            code = self.code_maker(prefix, str(num), num_length)
                            r['code_path'] = os.path.join(barcode_path, code+".png")
                            labels.append(HerbLabel(r))
                        else:
                            labels.extend([HerbLabel(r)]*r['duplicatesOfLabel'])
                # if the field value not a valid number, default repeat = 1
                except:
                    if start_code:
                        code = self.code_maker(prefix, str(num), num_length)
                        r['code_path'] = os.path.join(barcode_path, code+".png")
                        labels.append(HerbLabel(r))
                        del r['code_path']
                        r['catalogNumber'] = code
                        new_table = new_table.append(r, ignore_index=True)
                        num += 1
                    else:
                        if r['catalogNumber'] != "":
                            prefix, num, num_length = self.barcode_analyzer(r['catalogNumber'])
                            code = self.code_maker(prefix, str(num), num_length)
                            r['code_path'] = os.path.join(barcode_path, code+".png")
                        else:
                            pass
                        labels.append(HerbLabel(r))
        elif isinstance(self.repeat, int):
            for r in records:
                if start_code:
                    for _ in range(self.repeat):
                        code = self.code_maker(prefix, str(num), num_length)
                        r['code_path'] = os.path.join(barcode_path, code+".png")
                        labels.append(HerbLabel(r))
                        del r['code_path']
                        r['catalogNumber'] = code
                        new_table = new_table.append(r, ignore_index=True)
                        num += 1
                else:
                    if r['catalogNumber'] != "" and self.repeat == 1:
                        prefix, num, num_length = self.barcode_analyzer(r['catalogNumber'])
                        code = self.code_maker(prefix, str(num), num_length)
                        r['code_path'] = os.path.join(barcode_path, code+".png")
                        labels.append(HerbLabel(r))
                    else:
                        labels.extend([HerbLabel(r)]*self.repeat)
        # svae the new records to new table
        # this table can be used to import to other herbarium systems
        if start_code:
            resort_columns = list(self.df.columns)
            new_table = new_table.reindex(columns=resort_columns)
            new_table.to_excel(os.path.join(self.path, "DarwinCore_Specimens.xlsx"), index=False)
        return labels

    def write_html(self, start_code=None, page_num=6, template='flora'):
        """
        Makes list of Mustache-templated HTML articles, then iterates over list
        to generate complete HTML code containing all of the articles.
        """
        count = 0
        labels = self.mustachify(start_code)
        renderer = pystache.Renderer()
        tpl_path = os.path.join(HERE, template + '.mustache')
        css_path = os.path.join(HERE, template + '.css')
        try:
            with open(tpl_path, 'r', encoding="utf-8") as f:
                tpl = f.read()
        except Exception as error:
            raise error
        parsed = pystache.parse(tpl)
        with open(self.outfile, 'w', encoding="utf-8") as fh:
            fh.write("<!DOCTYPE html><html><head><link rel=\"stylesheet\" href=\"" +
                     css_path + "\"/></head><body>")
            fh.write("<div class=\"item-wrapper\">")
            for l in labels:
                count += 1
                labeltext = renderer.render(parsed, l)
                fh.write(labeltext)
                if count % page_num == 0:
                    fh.write("</div><div class=\"item-wrapper\">")
            fh.write("</div></body></html>")

    def barcode_analyzer(self, barcode):
        p = re.compile(r"\d+")
        txtnum = p.findall(barcode)[-1]
        length = len(txtnum)
        prefix = barcode[:-length]
        return prefix, int(txtnum), length

    def code_maker(self, prefix, num_txt, num_length):
        codenum = "0" * (num_length - len(num_txt)) + num_txt
        code = "".join([prefix, codenum])
        self.encoder(code)
        return code

    def encoder(self, barcode):
        if platform.system() == 'Windows':
            code = Code128Encoder(barcode, options={'ttf_font':'arial.ttf', 'ttf_fontsize':28})
        else:
            code = Code128Encoder(barcode, options={'ttf_font':'Arial', 'ttf_fontsize':28})
        code.save(os.path.join(self.path,'barcodes', barcode+".png"))
