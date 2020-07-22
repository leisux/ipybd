from ipybd.core import RestructureTable
from ipybd.std_table_terms import PlantSpecimenTerms, KingdoniaPlantTerms


# 对于同一个领域，不同方向的表格，可以先定义一个父类
# 该父类会被用于帮助其子类指向相应的列名别名库和可选值别名库
class Biodiversity(RestructureTable):
    pass

class PlantSpecimen(Biodiversity):
    def __init__(self, io):
        self.std_columns = PlantSpecimenTerms
        super(PlantSpecimen, self).__init__(io)

class KingdoniaPlant(Biodiversity):
    def __init__(self, io):
        self.std_columns = KingdoniaPlantTerms
        super(KingdoniaPlant, self).__init__(io, fcol = True)


if __name__ == "__main__":
    s = PlantSpecimen(r"/Users/xuzhoufeng/Downloads/test.xlsx")
    s.df.to_excel(r"../testfile/ttt.xlsx")
