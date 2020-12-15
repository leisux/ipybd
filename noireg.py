import os
from ipybd.noi import Link
from ipybd import NoiOccurrence
import json


# 这里请自行设置 NOI 账户生成的 API accesskey 和 secretkey
# 可以登录网页端 NOI 账户，在个人中心 API 栏目获得
acc = ""
sec = ""

# 这里设置数据路径
# 可以是 .txt .json .xlsx .xls .csv 文件路径
# 如果是 JSON 文件，数据结构必须符合 NOI Occurrence 类的规范
path = r"/Users/Downloads/moss.json"
path_elements = os.path.splitext(path)

# 如果上面路径是其他格式，程序会引导用户清洗和转换数据
# 对于达标的数据，程序会生成 ready.json 结尾的json 文件，
# 对于不达标的数据，会在原文件路径下生成 unvalid.json 和 need_check.json 文件
# unvalid 文件属于数据结构不达标，无法上传的数据，常见于必要字段的缺失,
# need_check.json 文件，是指字段值有疑异的数据，
# 该文件可核查后继续传递给 path 变量，以再次执行注册。
if path_elements[1] != '.json':
    datas = NoiOccurrence(path)
    datas.write_json()
    path = path_elements[0] + '_ready.json'

try:
    # 将 json 数据转换为 python 对象
    with open(path, encoding="utf-8") as json_datas:
        records = json.load(json_datas)
    # 执行注册
    # 注册完毕后，如果有未能成功注册的数据
    # 程序会在原路径下生成相应的 unpost.json 文件
    # 这些数据有可能是因为网络原因，也有可能是因为数据
    # 本身的原因，未能成功注册，可排查后再次提交给 path
    # 重新执行注册
    if input("是否立即执行 NOI 注册？(y/n):\n") == "y":
        link = Link(records, path_elements[0], acc, sec)
        link.register()
except FileNotFoundError:
    print("\n未能找到达标的数据文件\n")

