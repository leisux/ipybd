### 创建 BioName 实例

`BioName` 类可接受由拉丁学名构成的 `tuple`、`list`或`Pandas.Series` 等可迭代对象进行实例化：

```python
from ipybd import BioName

poa = BioName(["Poaceae", "Poa", "Poa annua", "Poa annua Schltdl. & Cham.", "Poa annua L.", None])
```
参与实例化的学名可以包含命名人（命名人的写法可随意），也可以不包含命名人（但包含命名人可以提高匹配精度），文本格式可以比较规范，也可以是不太规范的人工转录学名（但不能简写属名或种名）。

BioName 实例主要通过 `get`方法配合关键字从 [powo](http://www.plantsoftheworldonline.org/)、[ipni](www.ipni.org)、[中国生物物种名录](www.sp2000.org.cn) 获取相关学名的分类阶元、分类处理、物种图片、发表文献、相关异名等数据 。下面以获取上文 `poa` 实例对象在`powo`平台上的科属地位为例：

### 在线比对学名

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

`BioName` 提供了非常自由的数据操作空间，如果希望程序自动将查询的结果直接写入表格等数据框，可参考 `FormatDataset` 对象相关的[学名处理](./FORMATDATASET.md#学名处理)方法。