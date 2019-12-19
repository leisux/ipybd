# -*- coding: utf-8 -*-
# Based on python 3

from os import system as os_system
import _locale
from tkinter import Tk
from tkinter.filedialog import askdirectory, askopenfilename
import Kingdonia
import CVH

_locale._getdefaultlocale = (lambda *args: ['en_US', 'utf8'])

os_system("") #解决windows 10 cmd 命名行无法显示彩色文本的问题，神经质的一个方式竟然可行！


def main():
    print("\n\033[1;32miHerbarium 0.9.2，本软件许可遵从 GNU General Public License v3.0\
        \n\033[1;32m本软件 Github 项目地址未：https://github.com/leisux/iHerbarium\033[0m\
        \n\033[1;32m本软件由 NSII 项目资助，中国科学院昆明植物研究所标本馆（KUN）开发\033[0m\n")
        
    start = "y"
    while start == "y":
        opr = input(
            "\n请输入对应的数字，回车后选定所要进行的操作：\n\n【1】图片条码识别并命名\t\t【2】图片提取\t\t【3】Excel 标本数据纠错\
            \n\n【4】任意 Excel 标本数据表转 Kingdonia 格式\t\t【5】Kingdonia 格式转 CVH 格式\n\n")
        if opr == "1":
            print("\n请选择图片所在的文件夹，可以包括多层子文件夹，程序会自动忽略非图片文件\n")
            dir = askdir()
            if dir == "":
                continue
            Kingdonia.rename(dir)
        elif opr == "2":
            print("\n请选择需要匹配的 excel 文件\n\n")
            excel = askfile()
            if excel == "":
                continue
            print(excel)
            print("\n请选择进行匹配的图片文件夹路径：\n\n")
            dir = askdir()
            while dir == "":
                dir = askdir()
            print(dir)
            print("\n请选择被提取图片的存储路径：\n\n")
            dst = askdir()
            print(dst)
            Kingdonia.extract_file(excel, dir, dst)
        elif opr == "3":
            print("\n请选择需要核查的 excel 文件\n\n")
            excel = askfile()
            if excel == "":
                continue
            print(excel)
            Kingdonia.dwc_to_kingdonia(excel, "DWC")
        elif opr == "4":
            print("\n请选择需要核查的 excel 文件\n\n")
            excel = askfile()
            if excel == "":
                continue
            print(excel)
            Kingdonia.dwc_to_kingdonia(excel, "Kingdonia")
        elif opr == "5":
            print("\n请选择需要核查的 excel 文件\n\n")
            excel = askfile()
            if excel == "":
                continue
            print(excel)
            CVH.kingdonia_fieds2cvh(excel)
        else:
            input("\n您的输入内容不匹配...\n\n")
        start = input("\n请问是否继续操作（y/n）\n\n")


def askdir():
    root = Tk()
    root.withdraw()
    return askdirectory()


def askfile():
    root = Tk()
    root.withdraw()
    return askopenfilename()


if __name__ == "__main__":
    main()