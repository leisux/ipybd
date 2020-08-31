
ipybd 是一款生物多样性数据清洗、统计与分析程序包。ipybd 当前版本已经实现了完整的数据 ETL 流程，能够有效应对各类脏数据，可以大幅提高众源数据的整理、清洗、整合的效率和品质：

1. 可以通过物种名称，批量获取 [POWO](http://www.plantsoftheworldonline.org/), [IPNI](https://www.ipni.org/), [中国生物物种名录](http://www.sp2000.org.cn/)上相应的分类阶元、分类处理、物种图片、发表文献、相关异名等数据；
2. 可对各类手工转录的经纬度、中文行政区划、人名、拉丁学名、日期与时间、各类点选值（如植物习性）、各类数值/数值区间（如海拔）进行自动化的清洗、校正和转换；
3. 可将绝大多数生物多样性数据表转换为符合 DWC 规范的数据表，实现众源数据的高效 ETL；
4. 可以快速定制个性化的数据模板，实现相关数据到该数据模板的转换；

### 一、安装方法

可以直接在线通过 pip 在本机 Python 环境中安装 ipybd：

```python
pip install ipybd
```
或者将程序包 Clone 到本地后，在终端内进入 ipybd 目录，然后运行：

```python
pip install .
```



### 二、BioName

BioName 类可接受单个学名字符串、`tuple`、`list`或`Pandas.Series` 类型的学名字符串序列实例化对象：

```python
from ipybd import BioName

poa = BioName(["Poaceae", "Poa", "Poa annua", "Poa annua Schltdl. & Cham.", "Poa annua L.", None])
```
参与实例化的学名可以包含命名人（命名人的写法没有要求），也可以不包含命名人（但包含命名人可以提高匹配精度），学名格式可以比较规范，也可以是不太规范的人工转录学名（但不能简写属名）。

BioName 实例主要通过 `get`方法配合关键字从 [powo](http://www.plantsoftheworldonline.org/)、[ipni](www.ipni.org)、[中国生物物种名录](www.sp2000.org.cn) 获取相关学名的分类阶元、分类处理、物种图片、发表文献、相关异名等数据 。下面以获取上文 `poa` 实例对象在`powo`平台上的科属地位为例：

```python
poa.get('powoName')

# 程序返回结果
[
  ('Poaceae', 'Barnhart', 'Poaceae'),
 	('Poa', 'L.', 'Poaceae'),
 	('Poa annua', 'L.', 'Poaceae'),
 	('Poa annua', 'Schltdl. & Cham.', 'Poaceae'),
 	('Poa annua', 'L.', 'Poaceae'),
 	(None, None, None)
]

```
默认返回的结果是以元组为元素的 `list` 对象，`list`对象中的各检索结果与检索词的位置一一对应，对于没有检索结果的值，则以`None`值补充并与其他各检索结果对齐，以方便直接将返回结果转换成表格的行列；若希望以 `dict`对象返回，在请求时则可以通过`typ`参数指定：

```python
poa.get('powoName', typ=dict)  

#程序返回结果
{
  'Poaceae': ('Poaceae', 'Barnhart', 'Poaceae'),
 	'Poa': ('Poa', 'L.', 'Poaceae'),
 	'Poa annua': ('Poa annua', 'L.', 'Poaceae'),
 	'Poa annua Schltdl. & Cham.': ('Poa annua', 'Schltdl. & Cham.', 'Poaceae'),
 	'Poa annua L.': ('Poa annua', 'L.', 'Poaceae')
}
```

除了上述示例中的`powoName`参数，目前`BioName`的`get`方法总共支持以下九类需求：

+ `'powoName'`: 获取 powo 平台相应学名的科属地位、学名简写和命名人信息；

+ `'powoImages'`: 获取 powo 平台相应学名的物种图片地址，每个物种返回三张图片地址；

+ `'powoAccepted'`: 获取 powo 平台相应学名的接受名；

+ `'ipniName'`: 获取 ipni 平台相应学名的科属地位、学名简写和命名人信息；

+ `'ipniReference'`: 获取 ipni 平台相应学名的发表文献信息；

+ `'colName'`: 获取相应学名在中国生物物种名录中的科属地位、学名简写和命名人信息；

+ `'colTaxonTree'`: 获取相应学名在中国生物物种名录中的完整的分类学阶元信息；

+ `'colSynonyms'`: 获取相应学名在中国生物物种名录中的异名信息;

+ `'stdName'`: 优先获取中国生物物种名录的名称信息，如果无法获得，则获取`ipni`的信息。 

使用时，只需将上例`get`方法中的相应关键字替换为所需关键字即可。

### 三、FormatTable

FormatTable 类可以对 Biodiversity 相关的各类数据表的结构和值进行各种格式化处理。目前其可接受一个 Excle 或者 CSV 路径实例化对象：

```python
collections = FormatTable(r"~/Documents/record2019-09-10.xlsx") 
```

#### 3.1 学名处理

FormatTable 类基于 BioName 实例封装了一些学名处理方法，以使得在应对各种单纯基于数据表的名称处理能够更加简单和灵活，比如对于上述 `collections` 数据表，若表中的学名并非一列，而是按照 `"属名"`、`"种名"`、`"种下单元"`、`"命名人"`四列分开存储，ForamtTable 实例仍然可以直接进行学名查询：

```python
collections.get_ipni_name("属名", "种名", "种下单元", "命名人")

#返回结果
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

你也可以按照上述方式，根据自己的数据表结构传递自己的查询参数。目前 FormatTable 共支持以下几种名称处理方法：

+ `get_powp_name`: 获取 powo 平台相应学名的科属地位、学名简写和命名人信息；

+ `get_powo_images`: 获取 powo 平台相应学名的物种图片地址，每个物种返回三张图片地址；

+ `get_powo_accepted`: 获取 powo 平台相应学名的接受名；

+ `get_ipni_name`: 获取 ipni 平台相应学名的科属地位、学名简写和命名人信息；

+ `get_ipni_reference`: 获取 ipni 平台相应学名的发表文献信息；

+ `get_col_name`: 获取相应学名在中国生物物种名录中的科属地位、学名简写和命名人信息；

+ `get_col_taxontree`: 获取相应学名在中国生物物种名录中的完整的分类学阶元信息；

+ `get_col_Synonyms`: 获取相应学名在中国生物物种名录中的异名信息。

如果并不希望程序直接返回检索结果，而是想直接将名称的查询结果写入`collections`数据表，请求时可以将`concat`参数设置为`True`:

```python
collections.get_ipni_name("属名", "种名", "种下单元", "命名人", concat=True)

```

整合后的数据表，可以直接将数据表保存为文件：

```python
collections.save_table(r"~/Documents/new_record.xlsx")
```

#### 3.2 中文行政区划清洗和转换

```
collections.format_admindiv
```
#### 3.3 日期和时间清洗和转换

```
collections.format_datetime
```
#### 3.4 经纬度清洗和转换

```
collections.format_latlon
```
#### 3.5 数值及数值区间的清洗和转换

```
collections.format_number
```
#### 3.6 重复值标注

```
collections.mark_repeat
```
#### 3.7 数据列的分割

```
collections.split_columns
```

#### 3.8 数据列的合并

```
collections.merge_columns
```



### 四、RestructureTable 类定制数据模版

#### 4.1 OccurrenceRecord

#### 4.2 KingdoniaPlant



### 五、基于 Pandas 的数据统计与分析生态



### 六、特别声明

1. Ipybd 遵从 GNU General Public License v3.0 许可    
2. 本软件由 NSII 资助，© 徐洲锋，中国科学院昆明植物研究所

