"""
Author: 20171202, M Maher; 20201030, Xu Zhoufeng

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
from ipybd.table.terms import HerbLabelTerms
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
        self.labels = os.path.join(self.path, 'Labels.html')
        self.style = os.path.join(self.path, 'Style.css')

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
                                "./barcodes", code+".png")
                            labels.append(HerbLabel(r))
                            del r['code_path']
                            r['catalogNumber'] = code
                            new_table = new_table.append(r, ignore_index=True)
                            num += 1
                    else:
                        if r['catalogNumber'] != "" and r['duplicatesOfLabel'] == 1:
                            prefix, num, num_length = self.barcode_analyzer(
                                r['catalogNumber'])
                            code = self.code_maker(
                                prefix, str(num), num_length)
                            r['code_path'] = os.path.join(
                                "./barcodes", code+".png")
                            labels.append(HerbLabel(r))
                        else:
                            labels.extend([HerbLabel(r)] *
                                          r['duplicatesOfLabel'])
                # if the field value not a valid number, default repeat = 1
                except:
                    if start_code:
                        code = self.code_maker(prefix, str(num), num_length)
                        r['code_path'] = os.path.join(
                            "./barcodes", code+".png")
                        labels.append(HerbLabel(r))
                        del r['code_path']
                        r['catalogNumber'] = code
                        new_table = new_table.append(r, ignore_index=True)
                        num += 1
                    else:
                        if r['catalogNumber'] != "":
                            prefix, num, num_length = self.barcode_analyzer(
                                r['catalogNumber'])
                            code = self.code_maker(
                                prefix, str(num), num_length)
                            r['code_path'] = os.path.join(
                                "./barcodes", code+".png")
                        else:
                            pass
                        labels.append(HerbLabel(r))
        elif isinstance(self.repeat, int):
            for r in records:
                if start_code:
                    for _ in range(self.repeat):
                        code = self.code_maker(prefix, str(num), num_length)
                        r['code_path'] = os.path.join(
                            "./barcodes", code+".png")
                        labels.append(HerbLabel(r))
                        del r['code_path']
                        r['catalogNumber'] = code
                        new_table = new_table.append(r, ignore_index=True)
                        num += 1
                else:
                    if r['catalogNumber'] != "" and self.repeat == 1:
                        prefix, num, num_length = self.barcode_analyzer(
                            r['catalogNumber'])
                        code = self.code_maker(prefix, str(num), num_length)
                        r['code_path'] = os.path.join(
                            "./barcodes", code+".png")
                        labels.append(HerbLabel(r))
                    else:
                        labels.extend([HerbLabel(r)]*self.repeat)
        # svae the new records to new table
        # this table can be used to import to other herbarium systems
        if start_code:
            resort_columns = list(self.df.columns)
            new_table = new_table.reindex(columns=resort_columns)
            new_table.to_excel(os.path.join(
                self.path, "DarwinCore_Specimens.xlsx"), index=False)
        return labels

    def write_html(self, columns=2, rows=3, page_height=297, start_code=None, template='plant'):
        """
        Makes list of Mustache-templated HTML articles, then iterates over list
        to generate complete HTML code containing all of the articles.
        """
        count = 0
        page_num = columns * rows
        label_height = int((page_height - rows + 1)/rows)
        labels = self.mustachify(start_code)
        renderer = pystache.Renderer()
        tpl_path = os.path.join(HERE, template + '.mustache')
        css_path = os.path.join(HERE, template + '.css')
        try:
            with open(css_path, 'r', encoding="utf-8") as f:
                style = f.read()
            with open(self.style, 'w', encoding="utf-8") as f:
                f.write(style)
                f.write(
                    "\n\n.label-item {\n  min-height: 100px;\n  height: "+str(label_height)+"mm;\n}")
                f.write("\n\n\
@media print {\n  \
  body {\n  \
  display: block;\n\
  }\n\
  .item-wrapper {\n  \
    display: grid;\n  \
    grid-template-columns: repeat("+str(columns)+", 1fr);\n  \
    grid-template-rows: repeat("+str(rows)+", auto) !important;\n  \
    page-break-after: always;\n\
  }\n\
  article:nth-child(n) {\n  \
    border-right: 1px dashed rgb(230, 230, 230);\n\
  }\n\
  article:nth-child("+str(columns)+"n) {\n  \
    border-right: None\n\
  }\n\
  article:nth-child(n+"+str(columns+1)+") {\n  \
    border-top: 1px dashed rgb(230, 230, 230);\n\
  }\n\
  article:nth-child("+str(page_num)+"n) {\n  \
    page-break-after: always;\n\
  }\n\n\
}\n\n\
@page {\n\
  size:  auto;\n\
  margin: 0mm;\n\
}"
                )
            with open(tpl_path, 'r', encoding="utf-8") as f:
                tpl = f.read()
        except Exception as error:
            raise error
        parsed = pystache.parse(tpl)
        with open(self.labels, 'w', encoding="utf-8") as fh:
            fh.write(
                "<!DOCTYPE html><html><head><link rel=\"stylesheet\" href=\"./Style.css\"/><meta charset=UTF-8></head><body>")
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
            code = Code128Encoder(
                barcode, options={'ttf_font': 'arial.ttf', 'ttf_fontsize': 32})
        else:
            code = Code128Encoder(
                barcode, options={'ttf_font': 'Arial', 'ttf_fontsize': 32})
        code.save(os.path.join(self.path, 'barcodes', barcode+".png"))
