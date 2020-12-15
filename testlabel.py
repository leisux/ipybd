#!/usr/bin/python
# -*- coding=utf8 -*-
"""
# @Author : Xu Zhoufeng
# @Created Time : 2020-10-20 18:02:36
# @Description :
"""


from ipybd import Label


printer = Label(r"C:\Users\xu_zh\OneDrive\PDP\testfile\cvh.xlsx", repeat=2)
printer.write_html(start_code="KUN004123", page_num=8)


