from ipybd.std_table_terms import PlantSpecimenTerms
from ipybd.std_table_objects import PlantSpecimen
from os.path import dirname as path_dirname
from os.path import join as path_join
from tkinter import Tk
from tkinter.filedialog import askdirectory, askopenfilename
import Kingdonia


def main():
    print("iHerbarium 0.9.3，本软件许可遵从 GNU General Public License v3.0\
        \n本软件 Github 项目地址：https://github.com/leisux/iHerbarium\
        \n本软件由 NSII 项目资助，中国科学院昆明植物研究所标本馆（KUN）开发\n")
        
    start = "y"
    while start == "y":
        opr = input(
            "\n请输入对应的数字，回车后选定所要进行的操作：\n\n\
            【1】全表执行自动标准化\t\t【2】标记重复数据【】\
            【2】学名拼写检查\t\t【3】获取学名的分类阶元\n\n\
            【4】获取学名的接受名\t\t【5】获取学名的异名【6】获取学名的文献出处\n\n\
            【7】获取学名的分布地点【8】获取学名的标本影像\t\t\n\n\
            \n\
            【9】经纬度清洗\t\t【10】中国行政区划清洗\t\t【11】日期清洗\
            \n\
            【9】识别图片条码并以此命名图片\t\t【10】根据特定的文件名列表批量提取图片\n\n\
            \n\
            【10】表格转 Kingdonia 输入格式\t\t【11】表格转 CVH 数据格式\n\n")
        if opr == "3":
            print("\n请选择需要核查的 excel 文件\n\n")
            excel = askfile()
            if excel == "":
                continue
            print(excel)
            table = PlantSpecimen(excel, PlantSpecimenTerms)
            table.to_excel(path_join(path_dirname(excel), "NewTable.xlsx"), index=False)
        elif opr == "1":
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
        start = input("\n\n请问是否继续操作（y/n）\n\n")


def askdir():
    root = Tk()
    root.withdraw()
    return askdirectory()


def askfile():
    root = Tk()
    root.withdraw()
    return askopenfilename()



if __name__ == "__main__":
    s = PlantSpecimen(r"/Users/xuzhoufeng/Downloads/lbg-不合格.xlsx", PlantSpecimenTerms)
    s.df.to_excel(r"../testfile/ttt.xlsx")
