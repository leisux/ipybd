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
from PIL import Image, ImageDraw, ImageFont
from ipybd.core import RestructureTable
from ipybd.label.herb_label import HerbLabel
from ipybd.table.terms import HerbLabelTerms
from pystrich.code128 import Code128Encoder

HERE = os.path.dirname(__file__)

# CSTR 标识符前缀：二维码内容以这些前缀开头时，数据表派生 objectCSTR 字段
CSTR_PREFIXES = ('https://cstr.cn/', 'https://www.cstr.cn/')


class Label(RestructureTable):
    """Generate printable herbarium specimen labels.

    Converts specimen data from CSV/Excel to HTML labels using
    Mustache templates. Supports barcode generation and multiple
    copies per record.

    Args:
        io: Path to CSV/Excel file containing specimen data.
        repeat: Number of copies per record. If 0, uses duplicatesOfLabel field.
    """

    columns_model = HerbLabelTerms

    def __init__(self, io, repeat=0, cut=False):
        """Initialize Label generator.

        Args:
            io: Path to CSV/Excel file containing specimen data.
            repeat: Number of copies per record. If 0, uses
                    duplicatesOfLabel field.
            cut: If True, drop source columns not defined in the label
                 model after rebuilding. If False, keep them appended
                 after the model columns.
        """
        super(Label, self).__init__(io, fields_mapping=True, cut=cut, fcol="")
        self.repeat = repeat
        self.io = io
        self.path = os.path.splitext(io)[0]
        self.labels = os.path.join(self.path, 'Labels.html')
        self.style = os.path.join(self.path, 'Style.css')

    def to_dict(self):
        """Convert DataFrame to list of dictionaries.

        Returns:
            List of dictionaries representing records.
        """
        records = list(self.df.to_dict(orient='records'))
        for record in records:
            for key, value in record.items():
                # null value fill ""
                if pd.isnull(value):
                    record[key] = ""
        return records

    def mustachify(self, start_code=None, id_name="catalogNumber", copies_name="duplicatesOfLabel", base_url=None, logo_path=None):
        """Convert records to Mustache-templated label objects.

        Args:
            start_code: Starting barcode number for auto-generation.
            id_name: Column name for record ID.
            copies_name: Column name for duplicate count.
            base_url: Optional URL prefix. If provided, a QR code of
                      base_url + code is generated for each record.
                      If None, Code128 barcodes are generated as before.
                      If the prefix starts with https://cstr.cn/ or
                      https://www.cstr.cn/, an objectCSTR field with the
                      text after the prefix plus code is derived: it is
                      written to the original table when start_code is
                      empty, otherwise to DarwinCore_Specimens.xlsx.
            logo_path: Optional logo image path embedded in the QR center.
                       Defaults to ipybd/lib/cstr.ico.

        Returns:
            List of HerbLabel objects.
        """
        self.base_url = base_url
        self.logo_path = logo_path
        # CSTR 前缀识别：仅在二维码模式下派生 objectCSTR 字段
        cstr_suffix = self._cstr_suffix(base_url) if base_url else None
        records = self.to_dict()
        # 无 start_code 时沿用原编号：提前为每条记录派生 objectCSTR，
        # 打印结束后写回原始数据表
        if not start_code and cstr_suffix is not None:
            for r in records:
                code = r.get(id_name)
                if code:
                    r['objectCSTR'] = cstr_suffix + str(code)
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
            new_table = []
        if self.repeat == 0:
            for r in records:
                try:
                    if start_code:
                        for _ in range(r[copies_name]):
                            code = self.code_maker(
                                prefix, str(num), num_length)
                            # add code image path to HerbLabel instance properties
                            # then the code image will be linked to the label
                            r['code_path'] = os.path.join(
                                "./barcodes", code+".png")
                            # 先写入新编号，再构造标签对象，确保标签上的
                            # catalogNumber 属性与条形码一致
                            r[id_name] = code
                            if cstr_suffix is not None:
                                r['objectCSTR'] = cstr_suffix + code
                            labels.append(HerbLabel(r))
                            del r['code_path']
                            new_table.append(r.copy())
                            num += 1
                    else:
                        if r[id_name] != "" and r[copies_name] == 1:
                            prefix, num, num_length = self.barcode_analyzer(
                                r[id_name])
                            code = self.code_maker(
                                prefix, str(num), num_length)
                            r['code_path'] = os.path.join(
                                "./barcodes", code+".png")
                            labels.append(HerbLabel(r))
                        else:
                            labels.extend([HerbLabel(r)] *
                                          r[copies_name])
                # if the field value not a valid number, default repeat = 1
                except:
                    if start_code:
                        code = self.code_maker(prefix, str(num), num_length)
                        r['code_path'] = os.path.join(
                            "./barcodes", code+".png")
                        # 先写入新编号，再构造标签对象，确保标签上的
                        # catalogNumber 属性与条形码一致
                        r[id_name] = code
                        if cstr_suffix is not None:
                            r['objectCSTR'] = cstr_suffix + code
                        labels.append(HerbLabel(r))
                        del r['code_path']
                        new_table.append(r)
                        num += 1
                    else:
                        if r[id_name] != "":
                            prefix, num, num_length = self.barcode_analyzer(
                                r[id_name])
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
                        # 先写入新编号，再构造标签对象，确保标签上的
                        # catalogNumber 属性与条形码一致
                        r[id_name] = code
                        if cstr_suffix is not None:
                            r['objectCSTR'] = cstr_suffix + code
                        labels.append(HerbLabel(r))
                        del r['code_path']
                        new_table.append(r.copy())
                        num += 1
                else:
                    if r[id_name] != "" and self.repeat == 1:
                        prefix, num, num_length = self.barcode_analyzer(
                            r[id_name])
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
            # objectCSTR 由二维码内容派生：紧随编码列，便于对照
            if cstr_suffix is not None and 'objectCSTR' not in resort_columns:
                if id_name in resort_columns:
                    resort_columns.insert(
                        resort_columns.index(id_name) + 1, 'objectCSTR')
                else:
                    resort_columns.append('objectCSTR')
            new_table = pd.DataFrame(new_table)
            new_table = new_table.reindex(columns=resort_columns)
            new_table.to_excel(os.path.join(
                self.path, "DarwinCore_Specimens.xlsx"), index=False)
        elif cstr_suffix is not None:
            # 无 start_code：将派生的 objectCSTR 写回原始数据表
            self.__write_object_cstr_back(records, cstr_suffix)
        return labels

    def _cstr_suffix(self, base_url):
        """提取 base_url 中 CSTR 前缀之后的文本。

        base_url 以 https://cstr.cn/ 或 https://www.cstr.cn/ 开头时，
        返回前缀之后的文本（与编码拼接即为 CSTR 标识符）；否则返回 None，
        表示不需要派生 objectCSTR 字段。

        Args:
            base_url: 二维码 URL 前缀。

        Returns:
            CSTR 前缀之后的文本，或 None。
        """
        for prefix in CSTR_PREFIXES:
            if base_url.startswith(prefix):
                return base_url[len(prefix):]
        return None

    def __write_object_cstr_back(self, records, cstr_suffix):
        """将派生的 objectCSTR 写回原始数据表文件。

        用于未指定 start_code 的场景：标签沿用原编号，objectCSTR 按记录
        顺序写回输入文件；源表中已有的 objectCSTR 列会按记录更新。

        Args:
            records: mustachify 中按行顺序派生的记录字典列表。
            cstr_suffix: CSTR 前缀之后到编码之前的文本。
        """
        try:
            source = self.read_data(self.io)
        except Exception as error:
            print("\n提醒：无法读回原数据表，objectCSTR 未写入：{}\n".format(error))
            return
        try:
            values = {
                index: record.get('objectCSTR')
                for index, record in enumerate(records)
            }
            col = pd.Series(
                [values.get(index) for index in range(len(source))],
                index=source.index)
            if 'objectCSTR' in source.columns:
                source['objectCSTR'] = col.where(
                    col.notna(), source['objectCSTR'])
            else:
                source['objectCSTR'] = col
            ext = os.path.splitext(str(self.io))[1].lower()
            if ext in ('.xlsx', '.xls'):
                source.to_excel(self.io, index=False)
            elif ext == '.csv':
                source.to_csv(self.io, index=None, encoding='utf-8-sig')
            else:
                print("\n提醒：原数据表格式 {} 不支持写回，objectCSTR 未保存\n".format(
                    ext))
                return
            print("\nobjectCSTR 已写回原数据表：{}\n".format(self.io))
        except Exception as error:
            print("\n提醒：objectCSTR 写回原数据表失败：{}\n".format(error))

    def write_html(self, columns=2, rows=3, page_height=297, start_code=None, template='plant', id_name="catalogNumber", copies_name="duplicatesOfLabel", base_url=None, logo_path=None):
        """Generate HTML file with printable labels.

        Args:
            columns: Number of label columns per page.
            rows: Number of label rows per page.
            page_height: Page height in mm (e.g., 297 for A4).
            start_code: Starting barcode number.
            template: Template name (e.g., 'plant', 'flora_code').
            id_name: Column name for catalog number.
            copies_name: Column name for duplicate count.
            base_url: Optional URL prefix for QR code generation.
            logo_path: Optional logo image path for QR center.
        """
        count = 0
        page_num = columns * rows
        label_height = (page_height - (rows - 1)*0.5)/rows
        labels = self.mustachify(start_code, id_name, copies_name, base_url, logo_path)
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
    border-right: 0.5mm dashed rgb(230, 230, 230);\n\
  }\n\
  article:nth-child("+str(columns)+"n) {\n  \
    border-right: None\n\
  }\n\
  article:nth-child(n+"+str(columns+1)+") {\n  \
    border-top: 0.5mm dashed rgb(230, 230, 230);\n\
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
        """Parse barcode string into prefix, number, and length.

        Args:
            barcode: Barcode string containing prefix and number.

        Returns:
            Tuple of (prefix, number, length).
        """
        p = re.compile(r"\d+")
        txtnum = p.findall(barcode)[-1]
        length = len(txtnum)
        prefix = barcode[:-length]
        return prefix, int(txtnum), length

    def code_maker(self, prefix, num_txt, num_length):
        """Generate barcode string with zero-padded number.

        Args:
            prefix: Barcode prefix.
            num_txt: Number as string.
            num_length: Desired total length with zero-padding.

        Returns:
            Complete barcode string.
        """
        codenum = "0" * (num_length - len(num_txt)) + num_txt
        code = "".join([prefix, codenum])
        self.encoder(code)
        return code

    def encoder(self, barcode):
        """Generate barcode or QR code image file.

        When base_url is set, a QR code of base_url + barcode is
        generated with the bare barcode number printed below it.
        Otherwise a Code128 barcode is generated as before.

        Args:
            barcode: Barcode string to encode.
        """
        if getattr(self, 'base_url', None):
            self.qr_encoder(barcode)
        elif platform.system() == 'Windows':
            code = Code128Encoder(
                barcode, options={'ttf_font': 'arial.ttf', 'ttf_fontsize': 24})
            code.save(os.path.join(self.path, 'barcodes', barcode+".png"))
        else:
            code = Code128Encoder(
                barcode, options={'ttf_font': 'Arial', 'ttf_fontsize': 24})
            code.save(os.path.join(self.path, 'barcodes', barcode+".png"))

    def qr_encoder(self, code):
        """Generate QR code image for the label.

        The QR encodes base_url + code. The image is saved with the
        same file name convention as barcodes. When a logo image is
        available, it is embedded in the QR center with a white backing,
        using error correction level H to keep the code scannable.

        Args:
            code: Bare code string (e.g., 'P01234').
        """
        try:
            import qrcode
        except ImportError:
            raise ImportError(
                "生成二维码需要安装 qrcode 库，请执行: pip install qrcode")
        content = "".join([self.base_url, code])
        logo_path = getattr(self, 'logo_path', None)
        if not logo_path:
            # 默认依次尝试包内 lib 目录下的 logo 图片
            for name in ('cstr.png', 'cstr.ico'):
                candidate = os.path.join(HERE, os.pardir, 'lib', name)
                if os.path.isfile(candidate):
                    logo_path = candidate
                    break
        if logo_path and not os.path.isfile(logo_path):
            print("\n提醒：logo 文件不存在，跳过 logo 嵌入：{}\n".format(
                logo_path))
            logo_path = None
        box_size, border = 10, 4
        body_modules = None
        if logo_path:
            # 嵌入 logo 使用高容错等级 H（可容忍 30% 遮挡）
            from qrcode.constants import ERROR_CORRECT_H
            qr = qrcode.QRCode(
                error_correction=ERROR_CORRECT_H,
                box_size=box_size, border=border)
            qr.add_data(content)
            qr.make(fit=True)
            qr_img = qr.make_image().convert("RGB")
            body_modules = (qr.version - 1) * 4 + 21
            self.__embed_logo(
                qr_img, logo_path, box_size, border, body_modules)
        else:
            qr_img = qrcode.make(content).convert("RGB")
        qr_img.save(os.path.join(self.path, 'barcodes', code + ".png"))

    def __embed_logo(self, qr_img, logo_path, box_size, border, body_modules):
        """Embed a logo image in the center of the QR code.

        The logo keeps its aspect ratio when scaled: at most 30% of the
        QR body width, 22% of its height, and no more than twice its
        original size. It is placed on a white backing with padding and
        pasted at the QR center.
        """
        try:
            resample = Image.Resampling.LANCZOS
        except AttributeError:
            resample = Image.LANCZOS
        logo = Image.open(logo_path)
        logo.seek(0)
        logo = logo.convert("RGBA")
        body_px = body_modules * box_size
        max_w = int(body_px * 0.30)
        max_h = int(body_px * 0.22)
        ratio = min(max_w / logo.width, max_h / logo.height, 2.0)
        logo_w = max(int(logo.width * ratio), 16)
        logo_h = max(int(logo.height * ratio), 8)
        logo = logo.resize((logo_w, logo_h), resample)
        pad = max(2, min(logo_w, logo_h) // 10)
        backing = Image.new(
            "RGBA", (logo_w + pad * 2, logo_h + pad * 2),
            (255, 255, 255, 255))
        backing.paste(logo, (pad, pad), logo)
        offset = border * box_size
        cx = offset + body_px // 2
        cy = offset + body_px // 2
        qr_img.paste(
            backing,
            (cx - backing.size[0] // 2, cy - backing.size[1] // 2),
            backing)
