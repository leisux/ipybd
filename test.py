from ipybd import FormatTable, BioName

poa = poa = BioName(["Poaceae", "Poa", "Poa annua", "Poa annua Schltdl. & Cham.", "Poa annua L.", None])
# 检索 ipni.org 名称
poa.get('ipniName')

