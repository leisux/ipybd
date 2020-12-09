#!/usr/bin/python
# -*- coding=utf8 -*-
"""
# @Author : Xu Zhoufeng
# @Created Time : 2020-10-20 18:02:36
# @Description :
"""


from ipybd import Label


printer = Label(r"/Users/xuzhoufeng/Downloads/record2020-12-08.xlsx", repeat=2)
printer.write_html(start_code="HITBC004123", page_num=8)


