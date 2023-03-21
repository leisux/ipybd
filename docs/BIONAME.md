## 三、主要的数据处理方法

### 3.1 BioName

`BioName` 类可接受由拉丁学名构成的 `tuple`、`list`或`Pandas.Series` 等可迭代对象进行实例化：

```python
from ipybd import BioName

poa = BioName(["Poaceae", "Poa", "Poa annua", "Poa annua Schltdl. & Cham.", "Poa annua L.", None])
```
参与实例化的学名可以包含命名人（命名人的写法可随意），也可以不包含命名人（但包含命名人可以提高匹配精度），文本格式可以比较规范，也可以是不太规范的人工转录学名（但不能简写属名或种名）。

BioName 实例主要通过 `get`方法配合关键字从 [powo](http://www.plantsoftheworldonline.org/)、[ipni](www.ipni.org)、[中国生物物种名录](www.sp2000.org.cn) 获取相关学名的分类阶元、分类处理、物种图片、发表文献、相关异名等数据 。下面以获取上文 `poa` 实例对象在`powo`平台上的科属地位为例：

```python
poa.get('powoName')

Out:
[
  ('Poaceae', 'Barnhart', 'Poaceae'),
 	('Poa', 'L.', 'Poaceae'),
 	('Poa annua', 'L.', 'Poaceae'),
 	('Poa annua', 'Schltdl. & Cham.', 'Poaceae'),
 	('Poa annua', 'L.', 'Poaceae'),
 	(None, None, None)
]

```
默认返回的结果是以 `tuple` 为元素的 `list` 对象，`list`对象中的各检索结果与检索词的位置一一对应，对于没有检索结果的值，则以`None`值补充并与其他各检索结果对齐，以方便直接将返回结果转换成表格的行列；若希望以 `dict`对象返回，在请求时则可以通过`typ`参数指定：

```python
poa.get('powoName', typ=dict)  

Out:
{
  'Poaceae': ('Poaceae', 'Barnhart', 'Poaceae'),
 	'Poa': ('Poa', 'L.', 'Poaceae'),
 	'Poa annua': ('Poa annua', 'L.', 'Poaceae'),
 	'Poa annua Schltdl. & Cham.': ('Poa annua', 'Schltdl. & Cham.', 'Poaceae'),
 	'Poa annua L.': ('Poa annua', 'L.', 'Poaceae')
}
```

除了上述示例中的`powoName`参数，目前`BioName`的`get`关键字总共有 11 个，它们的作用分别是：

+ `'powoName'`: 获取 powo 平台相应学名的科属地位、学名简写和命名人信息；

+ `'powoImages'`: 获取 powo 平台相应学名的物种图片地址，每个物种返回三张图片地址；

+ `'powoAccepted'`: 获取 powo 平台相应学名的接受名；

+ `'tropicosName'`: 获取 tropicos.org 平台相应的学名；

+ `'tropicosAccepted'`: 或缺 tropicos.org 平台相应的接受名；

+ `'ipniName'`: 获取 ipni 平台相应学名的科属地位、学名简写和命名人信息；

+ `'ipniReference'`: 获取 ipni 平台相应学名的发表文献信息；

+ `'colName'`: 获取相应学名在中国生物物种名录中的科属地位、学名简写和命名人信息，需要特别注意：受限于 sp2000 接口的限制，若所检索的学名为异名，程序将无法判定检索结果的有效性而返回类似于无结果的 `None`；

+ `'colTaxonTree'`: 获取相应学名在中国生物物种名录中的完整的分类学阶元信息；

+ `'colSynonyms'`: 获取相应学名在中国生物物种名录中的异名信息;

+ `'stdName'`: 优先获取中国生物物种名录的名称信息，如果无法获得，则获取`ipni`的信息。 

使用时，只需将上例`get`方法中的相应关键字替换为所需关键字即可。

### 3.2 FormatDataset

`FormatDataset` 类是 `ipybd` 执行数据处理的核心类，也是 `ipybd` 数据模型类的父类。它提供了对生物多样性相关的各类数据集进行各种结构重构和值格式化处理的基本方法。普通用户也可以直接调用它以更加自主的方式处理个性化的数据集或者开发自己的脚本和程序。

#### 3.2.1 数据的载入

目前 FormatDataset 可接受一个 Excel、CSV、TXT、JSON、`Pandas.DataFrame`、RDBMS 数据库对象进行实例化：基于 Excel 、CSV 、TXT、JSON 实例化，可以直接传递相应文件的路径给 `FormatDataset`：

```python
collections = FormatDataset(r"~/Documents/record2019-09-10.xlsx") 
```

`FormatDataset` 默认采用 `UTF-8` 编码文件，如果传递 CSV 文件出现`UnicodeDecodeError`错误，可以尝试显式指定相应的编码方式，一般都可以得到解决（Python 支持的标准编码[戳这里](https://docs.python.org/3/library/codecs.html#standard-encodings)。此外，`ipybd` 的数据载入方式主要基于 `pandas.read_*`等方法封装，支持这些方法中绝大部分的参数传入，因此若遭遇一些特殊问题，也可以直接查看[`pandas`](https://pandas.pydata.org/)相应方法的说明。

```python
# 这里显式的指定了 csv 文件的编码方式为 gbk
collections = FormatDataset(r"~/Documents/record2019-09-10.cvs", encoding='gbk') 
```

如果已经有一个 `DataFrame` 对象，也可以直接传递给 `FormatDataset`：

```pythoon
collections = FormatDataset(DataFrame)
```
注意：使用 `DataFrame` 创建 `FormatDataset` 对象时，如果 `DataFrame` 索引有重复，请先重置索引。
基于本地或线上的关系型数据库创建 `FormatDataset` 实例，需要先创建数据库连接。在 python 生态中，比如广泛使用的 `MySQL`数据库就有诸如 mysqlclient、pymysql、mysql-connector 等多种连接库可以使用，下方示例演示的是通过 sqlalchemy 建立 mysql 数据库连接，个人可以根据喜好和使用的数据库自行选择相应的连接库创建连接器。

```python
# 首先导入相应的连接库
from sqlalchemy import create_engine

# 通过账户、密码、地址、端口等创建数据库连接器
# 这里演示了与我本地 mysql 中 ScientificName 数据库建立连接
conn = create_engine('mysql+pymysql://root:mypassward@localhost:3306/ScientificName')

# 然后建立检索数据库的 sql 语句，用于从数据库中筛选出需要的数据
# 这里的sql语句演示了从 ScientificName 数据库中调取 10 条 theplantlist 学名数据
sql = "select * from theplantlist limit 10;"

# 将 sql 语句和建立好的连接器传递给 ipybd.FormatDataset
tpl = FormatDataset(sql, conn)

# 执行完毕后，数据会以 DataFrame 结构保存到 tpl 实例的 df 对象之中
# 然后就可以在本地内存中对这些数据进行各种操作了
# 比如查看数据中的学名 id 、family、genus 和拉丁名信息
tpl.df[['_id', 'family', 'genus', 'latin']] 

Out:
                        _id          family        genus                 latin
0  59367c08ec325b77e9124490     Achariaceae                          Chilmoria
1  59367c08ec325b77e9124491                                        Achariaceae
2  59367c08ec325b77e9124492     Achariaceae    Chilmoria     Chilmoria odorata
3  59367c08ec325b77e9124494  Alseuosmiaceae                         Alseuosmia
4  59367c09ec325b77e9124495                                     Alseuosmiaceae
5  59367c09ec325b77e9124496  Alseuosmiaceae   Alseuosmia    Alseuosmia banksii
6  59367c09ec325b77e9124498   Allisoniaceae                        Calycularia
7  59367c09ec325b77e9124499                                      Allisoniaceae
8  59367c09ec325b77e912449a   Allisoniaceae  Calycularia  Calycularia compacta
9  59367c09ec325b77e912449c     Acanthaceae                        Acanthodium
```

#### 3.2.2 学名处理

`FormatDataset` 类基于 `BioName` 实例封装了一些学名处理方法，以便用户能够更便捷的对数据表中的名称进行处理。比如对于上述 `collections` 实例，若相关数据表中的学名并非单列，而是按照 `"属名"`、`"种名"`、`"种下单元"`、`"命名人"`四列分列存储，单纯使用 `BioName` 类需要用户先自行合并相应数据列才可以执行在线查询。而 `FormatDataset` 实例则可以直接进行学名的查询和匹配：

```python
# 这里以获取 ipni 平台的信息为例
# 调用 get_ipni_name 时，将构成学名的多个列名直接按序传递给方法即可执行检索
collections.get_ipni_name("属名", "种名", "种下单元", "命名人")

Out:
[
	('Clematis', 'L.', 'Ranunculaceae'),
 	('Crepis', 'L.', 'Asteraceae'),
 	('Krascheninnikovia ceratoides', '(L.) Gueldenst.', 'Chenopodiaceae'),
	('Apiaceae', 'Lindl.', 'Apiaceae'),
 	('Boerhavia', 'L.', 'Nyctaginaceae'),
 	('Aster', 'L.', 'Asteraceae'),
 	('Agropyron cristatum', '(L.) P.Beauv.', 'Poaceae'),
 	('Orostachys', 'Fisch.', 'Crassulaceae'),
 	('Ephedra', 'L.', 'Ephedraceae'),
 	('Elymus', 'Mitchell', 'Poaceae'),
 	('Aster', 'L.', 'Asteraceae'),
 	('Nitraria tangutorum', 'Bobrov', 'Zygophyllaceae'),
 	(None, None, None),
 	('Carissa', 'L.', 'Apocynaceae'),
 	('Pedicularis', 'L.', 'Scrophulariaceae'),
 	('Centaurea', 'L.', 'Asteraceae'),
 	...
 ]
```

如上所示，不同数据表的学名表示方式时常会有差异，而通过诸如`get_ipni_name`这样的实例方法可以大幅提高数据处理的便捷性和灵活性。目前 `FormatDataset` 实例共支持以下几种学名处理方法：

+ `get_powo_name`: 获取 powo 平台相应学名的科名、学名简写、命名人、ipniLsid；

+ `get_powo_images`: 获取 powo 平台相应学名的物种图片地址，每个物种返回三张图片地址；

+ `get_tropicos_Name`: 获取 tropicos.org 平台相应学名的科名、学名简写、命名人、nameid；

+ `get_tropicos_Accepted`: 或缺 tropicos.org 平台相应的接受名；

+ `get_powo_accepted`: 获取 powo 平台相应学名的接受名；

+ `get_ipni_name`: 获取 ipni 平台相应学名的科名、学名简写、命名人、ipniLsid；

+ `get_ipni_reference`: 获取 ipni 平台相应学名的发表文献信息；

+ `get_col_name`: 获取相应学名在中国生物物种名录中相应学名的科名、学名简写、命名人、namecode；

+ `get_col_taxontree`: 获取相应学名在中国生物物种名录中的完整的分类学阶元信息；

+ `get_col_synonyms`: 获取相应学名在中国生物物种名录中的异名信息;
  
+ `format_scientificname`: 规范物种学名格式。

如果在使用这些方法时，并不希望程序直接返回结果，而是想直接将查询结果写入`collections`数据表，请求时可以将`concat`参数设置为`True`:

```python
collections.get_ipni_name("属名", "种名", "种下单元", "命名人", concat=True)
```

如果需要将整合后的数据表存储为文件，可以调用`collections`实例的`save_data`方法：

```python
collections.save_data(r"~/Documents/new_record.xlsx")
```