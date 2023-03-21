### 特定数据集的结构重塑

将某一特定结构的数据集转换为另一种具有特定字段和结构的数据集，通常会涉及一系列的数据拆分、合并和字段更名。`ipybd` 将不同的数据集结构视为不同的数据模型，通过自定义数据模型，可以实现数据集结构的自动转换。这里以国内植物标本数据集中广泛使用的 CVH 数据表为例，CVH 的数据表包含了："采集人"、"采集号"、"采集日期"、"国家"、"省市"、“区县”、"属"、"种"、“命名人”、"种下等级"、“种下等级命名人” 等一系列字段。如果我们只想从 CVH 的数据表中提取一个包含"记录入"、"记录编号"、"记录时间"、"省"、"市"、"学名" （不含命名人）六个概要性字段的数据表，就可以通过 `ipybd` 自定义模型实现 CVH 数据表的自动转换：

```python
from ipybd import imodel    
from enum import Enum

@imodel 
class MyModel(Enum):
    记录人 = '$采集人'   
    记录编号 = '$采集号' 
    记录时间 = '$采集日期'
    省__市 = {'$省市':','}  
    学名 = ('$属', '$种', '$种下等级', ' ')  

```

上面代码通过 `ipybd` 的 `imodel` 修饰符，修饰了一个符合 `ipybd` 模型语义规范的枚举类。这样就可以生成一个自定义的 `MyModel` 数据模型。模型定义中，枚举元素的 `name` 为新数据集的字段名，枚举元素的 `value` 为该字段指代的数据对象。单纯的结构重塑中 `value` 的表达通常涉及三类操作：

+ **字段更名**：原数据集中的数据对象不用做任何改变，直接更名后映射到新的数据集中。上面代码中的`采集人`,`采集号`,`采集日期`就是通过更名表达式重新映射为新数据集中的`记录人`,`记录编号`,`记录时间`。其中 `$` 前缀在 `ipybd` 模型中用于修饰一个数据对象，带有该前缀的字符串会被认为是一个数据对象参数。因此 `记录人 = $采集人` 这样的表达式表示的就是：将原数据集中的`采集人`数据对象转换为新数据集中的`记录人`数据对象。

+ **数据拆分**：将原数据集中的单个数据对象拆分为新数据集中的多个数据对象。`ipybd` 通过 `dict` 类型表达拆分，比如上面代码中的 `省__市 = {'$省市':','}`  就是表示：将原数据集中的`省市`数据对象通过 `,` 分隔符拆分为新数据集中的`省`,`市`两个新数据对象。其中新分出的列名之间要以 `__` 进行连接。需要注意的是 `str` 类型的分隔符只会参与一次拆分，如果想要进行多次拆分，可以将多个分隔符组装为一个 `tuple` ，比如 `国__省__市__县 = {"$行政区划":(";", ";",";")}` 或者 `国__省__市__县 = {"$行政区划":(";",)*3}` 就表示将`行政区划`拆分为`国`,`省`,`市`,`县`四个新数据对象。

+ **数据合并**：将原数据集中的多个数据对象合并为单个数据对象。 `ipybd` 通过 `tuple` 类型表达合并，比如上面代码中的

  `学名 = ('$属', '$种', '$种下等级', ' ') ` 就表示将原数据集中的`属`,`种`,`种下等级`数据通过空格按序连接，合并为新数据集中的`学名`字段。合并表达式的最后一个元素为各个字段间的连接符。

当用一个 CVH 样式的 Excel 数据表实例化 `MyModel` 对象， 它会在内存中自动完成数据表结构的转换，生成一个符合模型定义的新的数据表：

```python
cvh = MyModel(r"/Users/.../cvh.xlsx") 

cvh.df.head()                                                                                                                                                          
Out: 
            记录人                    记录编号      记录时间    省     市                          学名
0    王雷,朱雅娟,黄振英    Beijing-huang-dls-0026  20070922   北京   北京市     Ostericum grosseserratum
1           NaN                      YDDXSC-022  20071028  云南省   临沧市   Boenninghausenia albiflora
2  欧阳红才,穆勤学,奎文康                YDDXSC-022  20071028  NaN     None   Boenninghausenia albiflora
3   吴福川,查学州,余祥洪                      NaN   20070512  湖南省  张家界市       Broussonetia kazinoki
4   吴福川,查学州,余祥洪               SCSB-07009   20070512  湖南省  张家界市       Broussonetia kazinoki

```

`MyModel` 模型默认会自动去除模型中未定义的数据对象，如果想要保留原始数据集中其他数据对象，可以在调用时传递相应关键字：

```python
cvh = MyModel(r"/Users/.../cvh.xlsx", cut=False) 
```

此外通过 `@imodel` 修饰生成的数据模型，都是前述 `FormatDataset` 的子类，因此 `FormatDataset` 实例具有的方法都可以被这些模型的实例直接调用。

### 众源数据集的结构重塑

除了针对特定数据集进行结构的转换，`ipybd` 数据模型还支持不同数据源到特定数据集结构的转换。相应数据模型的定义与上述数据模型的定义稍有不同：

```python
from enum import Enum
from ipybd import imodel

@imodel  
class MySmartModel(Enum):  
    记录人 = '$recordedBy'  
    记录编号 = '$recordNumber'  
    采集日期 = '$eventDate' 
    省__市 = {('$province', '$city'): ','} 
    学名 = ['$scientificName',  ('$genus', '$specificEpithet', '$taxonRank', '$infraspecificEpithet', ' ')] 
    
```

如上所示，对于具备字段映射功能的 `ipybd` 数据模型，其数据对象的表达不再是具体真实的字段名，而是采用了一套新的标准字段名以指代同一语义的不同字段名。比如上面代码中的 "recordedBy" 就可以同时指代"采集人"、"采集人员"、"记录人"、"记录者"、"记录人员"、"COLLECTOR" .... 等一批不同名称但意义相同的字段。`ipybd` 就是依靠这种标准字段名称的泛化关系实现了众源数据集结构的转换。目前 `ipybd` 的标准字段名称库主要基于 [DarwinCore](https://dwc.tdwg.org/terms/) 定义，其中也有部分字段名称会根据国内数据的现实情况，做了一些调整和扩展。标准字段名称库相当于一类对象的基本构成元素库。使用它进行模型的定义，会存在一些特殊的表达方式，比如上述 `MySmartModel` 模型中：

```python
省__市 = {('$province', '$city'): ','} 
```

与 `MyModel` 中`$省市`的表达方式就有很大差异：

```python
省__市 = {'$省市':','}
```

这是因为在 `ipybd` 的标准字段名称库中，并不存在与"省市"完全等同的标准字段名，而只存在 "province" 和 "city" 两个标准字段名。显然“省市”应该是由"province"和"city"两个标准字段组合而成，因此在 `MySmartModel`中就需要以表示合并语义的元组表达`$省市`这个概念。

同理，对于`学名`的表示：

```python
学名 = ['$scientificName',  ('$genus', '$specificEpithet', '$taxonRank', '$infraspecificEpithet', ' ')]
```

上面 `list` 中第二个元素，是表示学名也可能是由 “genus”、“specificEpithet”、“taxonRank”、“infraspecificEpithet” 四个字段以空格相间的形式组合而成。相对于 `dict` 表示元素拆分，`tuple` 表示元素的合并，**`list` 在 `ipybd` 数据模型的语义中则表示按需优先选择**，因此上面这行代码在 `ipybd` 数据模型定义中表示：`学名`优先采用与 `scientificName` 相对应数据对象，其次使用由多个字段组合而成的数据对象。

通过这种形式，`ipybd` 数据模型不仅可以实现同一对象不同名称的映射，还可以实现同一对象不同结构形式的映射，从而获得更加通用的数据自动处理能力。

具备字段映射能力的数据模型，不仅可以处理与模型结构相对应的数据集结构转换：

```python
# 3.1 中示范的 cvh 数据表，仍然可以通过 MySmartModel 执行数据结构转换
# 需要注意的是使用映射功能的模型，在调用时需要设置 fields_mapping=True
cvh = MySmartModel(r"/Users/.../cvh.xlsx", fields_mapping=True) 
cvh.df.head()

Out: 
            记录人                    记录编号      记录时间    省     市                          学名
0    王雷,朱雅娟,黄振英    Beijing-huang-dls-0026  20070922   北京   北京市      Ostericum grosseserratum
1           NaN                      YDDXSC-022  20071028  云南省   临沧市   Boenninghausenia albiflora
2  欧阳红才,穆勤学,奎文康                YDDXSC-022  20071028  NaN     None    Boenninghausenia albiflora
3   吴福川,查学州,余祥洪                      NaN   20070512  湖南省  张家界市       Broussonetia kazinoki
4   吴福川,查学州,余祥洪               SCSB-07009   20070512  湖南省  张家界市       Broussonetia kazinoki

```

还可以实现不同数据源的数据结构转换，比如不同于 CVH 的数据表，biotracks.cn 导出的数据集中省、市是分列的，同时学名也不是分开的，而是聚合的。这种差异明显的数据集，仍然可以通过 `MySmartModel` 实现结构的转换。
```python
bio = MySmartModel(r'/Users/.../biotracks.xlsx', fields_mapping=True)
bio.df.head()

Out: 
          记录人      记录编号        采集日期             省              市                  学名
0  刘恩德|182,徐洲锋|28  9125  2019-08-09 12:29:00  新疆维吾尔自治区 吐鲁番地                             Clematis
1  刘恩德|182,徐洲锋|28  9126  2019-08-09 12:33:00  新疆维吾尔自治区 吐鲁番地                               Crepis
2  刘恩德|182,徐洲锋|28  9128  2019-08-09 14:02:00  新疆维吾尔自治区 巴音郭楞蒙古自治州 Krascheninnikovia ceratoides
3  刘恩德|182,徐洲锋|28  9132  2019-08-09 14:25:00  新疆维吾尔自治区 巴音郭楞蒙古自治州                     Apiaceae
4  刘恩德|182,徐洲锋|28  9136  2019-08-09 15:01:00  新疆维吾尔自治区 巴音郭楞蒙古自治州                    Boerhavia

```

### 标准字段名映射引导

需要注意的是：`ipybd` 的字段映射完全基于内置的标准字段名称关系库，对于常见的标准字段别名`ipybd`通常可以自动完成对应，然而对于一些库中没有的别名，`ipybd` 会开启手动映射引导模式，以帮助用户完成数据集字段到标准字段的对应。通常引导模式会是这样的：

```
以下是还需通过手录表达式指定其标准名的原始表格表头：
1.海拔   2.属名   3.种的加词   4.种下阶元

请输入列名转换表达式，录入 0 忽略所有：   
```

上方的引导是告诉用户仍然有 4 个原数据集字段没有找到对应的标准字段名，需要用户通过表达式确定对应关系，比如对于上述`海拔`如果原始数据集中该字段内容其实是一个类似于`800-1000`这样的数值区间，那么你可能需要录入：

```python
1 = 64 - 66
```

其中 `1` 是上述`海拔`字段的序号，`64` 和  `66` 分别表示标准字段名称库中的`minimumElevationInMeters` 和 `maximumElevationInMeters` 编号，`-` 表示原始数据集中两个数值之间的实际连接符。因此`1 = 64 - 66 ` 就是表示将 `海拔` 以`-`为分隔符拆分为 `minimumElevationInMeters` 和 `MaximumElevationInMeters` 两个标准字段。其中 `minimumElevationInMeters` 和 `ma ximumElevationInMeters` 的编号可以通过输入'min/max/海拔' 等关键字后再按 `Tab` 键呼出下拉，用上下键选择获得：

![image](https://ftp.bmp.ovh/imgs/2020/12/16afd0e46666e6c2.png)

除了拆分，也会遇到需要合并的字段名，比如希望将上述 `2` `3` `4` 三个字段合并为学名，其表达式逻辑也是类似的：

```python
2 3 4 = 106
```

`2`, `3`, `4` 分别表示上述 `属名` `种的加词` `种下阶元` 的序号，`106` 表示标准字段名 `scientificName` 的编号。其中 `2` `3` `4` 之间的空格表示以空格作为连接符合并。（输入表达式的时候，输入完一个编号，按一次空格有利于简化编号下拉的步骤，同时对于非空格连接符，其前后的空格，程序也不会将其视为连接符的组成部分，因此可放心录入。

### 具有值处理功能的数据模型定义

简单的字段名映射、数据拆分与合并可以应付大多数数值规范的数据集结构重塑，但在面对各种来源的人工数据集时，单纯的数据集结构重塑还是无法满足数据的强一致性需求。事实上对于众源数据，尤其是人工梳理的数据，其数据结构和值的规范性其实很难保证严格一致。比如下方所示的物种分布数据集：

```python
import pandas

dirtydata = pandas.read_excel(r"/Users/.../dirtydata.xlsx")
dirtydata.head()

Out:
                              鉴定                       坐标        日期     海拔      国别  产地1   产地2
0                 Trifolium repens   N:28 34'478E:99 49 129"        1978   1400～1800  中国  HEB  承德市
1                        Lauraceae  N:27 55'E:99 36'          1982.08.24    1200-1300  中国   HN    吉首
2                      Glycine max  N:38 34'481"E:099 50'054"   19830500  大概400-600   中国   YN  勐腊县
3                     Glycine  N:24°35'51.22"; E:100°04 '52.96" 1983.6.31  1000-1100m  中国   YN    大理
4  Rubia cordifolia var. sylvatica  N 31°04′206″, E 96°58′476″    19820824     3800米  中国   SC  德格县

```

该数据集所有的内容采用的都是文本格式，同时经纬度、日期、海拔的写法也不统一，学名没有命名人，省份使用的是拼音简写...这样的人工数据集虽然表意明确，但对于数据库归档、数据分析等真正的应用而言，仍然是无法直接利用的。`ipybd` 可以定义具备严格数据类型校验和转换功能的数据模型，以自动化的处理这类脏数据梳理的问题：

```python

from ipybd import imodel
from ipybd import BioName, GeoCoordinate, DateTime, Number, AdminDiv
from enum import Enum

@imodel
class DataCleaner(Enum):  
    拉丁名 = BioName('$鉴定', style='scientificName')  # style 关键字参数指名返回带有完整命名人的学名
    经度__纬度 = GeoCoordinate('$坐标') 
    采集日期 = DateTime('$日期') 
    海拔1__海拔2 = {'$海拔':'-'} 
    海拔_海拔高 = Number('$海拔1', '$海拔2', int)   # int 位置参数指明返回 int 类型的数值
    国__省__市__县 = AdminDiv(('$国别', '$产地1', '$产地2', ','))  # ipybd 定义的元组等表达式都可以作为单个参数进行传递                                                                                                                                                             
```

相对于简单的结构转换模型，`DataCleaner` 的枚举值中不仅定义了`$`修饰的数据对象，还将这些对象传递给了诸如 `BioName` 这样的 `ipybd` 数据类。这些类会自动清洗相应的数据，并返回符合预期的结果：

```python
cleandata = DataCleaner(r"/Users/.../dirtydata.xlsx")
cleandata.df.head()                                                                                                                                                       
Out: 
             拉丁名           经度       纬度    采集日期    海拔  海拔高   国     省                 市      县
0 Trifolium repens L.      28.5746  99.8188    19780000  1400  1800  中国  河北省              承德市   None
1 Lauraceae                27.9167     99.6    19820824  1200  1300  中国  湖南省  湘西土家族苗族自治州   吉首市
2 Glycine max (L.) Merr.   38.5747  99.8342    19830500   400   600  中国  云南省    西双版纳傣族自治州   勐腊县
3 Glycine                  24.5976  100.081  !1983.6.31  1000  1100  中国  云南省       大理白族自治州   None
4 !Rubia cordifolia var. sylvatica 31.0701  96.9746 19820824  3800  3800  中国  四川省  甘孜藏族自治州   德格县
```

相比于原始的数据集，经过 `DataClean` 清洗的数据，值的格式更加规范统一，其中经纬度、海拔采用的是可以直接参与计算的十进制数数值类型，行政区划也被拆分为标准的四级行政区，学名附带有完整的命名人。而对于可能存在错误的数据，`ipybd` 会使用 “!” 标识原始数据以便于核实（上述学名 Rubia cordifolia var. sylvatica 被标注主要是因为该名称在中国生物物种名录中是一个异名）。目前，`ipybd` 总共提供了以下十个内置值处理类以供用户调用，在 `ipybd` 数据模型中使用这些类，最终均会返回一个 `DataFrame` 对象：

+ `BioName(names: Union[list, pd.Series, tuple], style='scientificName')`

  清洗学名，其中 `style` 关键字参数表示返回后的学名样式，默认返回带有命名人的完整学名，也可以设置为 `'simpleName'` 返回去命名人的拉丁名。

+ `AdminDiv(address: Union[list, pd.Series, tuple])`

  清洗`address`中的中文行政区划，最终返回由`country` `province` `city` `country` 组成的`DataFrame` 对象；对于非中文书写的地址会忽略。

+ `Number(min_column: Union[list, pd.Series, tuple], max_column: Union[list, pd.Series, tuple] = None, typ=float, min_num=0, max_num=8848)`

  清洗数值或数值区间，其`min_column`和`max_column`为需要处理的数值对象，`typ` 用于指定处理后返回的对象类型，支持 `int` 和 `float`，`min_num`和`max_num` 分别设置参与处理的数字大小下限和上限。

+ `GeoCoordinate(coordinates: Union[list, pd.Series, tuple])`

  严格的校验、清洗和转换经纬度，接收一个由经纬度文本组成的 `coordinates` 可迭代对象。

+ `DateTime(date_time: Union[list, pd.Series, tuple], style="num", timezone='+08:00')`

  清洗日期或带日期的时间，其中 `style` 指代最终返回的数据样式，默认输出纯数字文本日期，可重设为 `'utc'` `'date'` `'datetime'` 样式；`timezone` 为日期或时间所处的时区。

+ `HumanName(names: Union[list, pd.Series, tuple])`

+ 清洗人名，可以将中文人名中的空格清除，并判断长度的合理性，同时可以将常见西文人名的书写格式统一规范化。

+ `UniqueID(*columns: pd.Series)`

  标注重复值，可根据一列或多列 `pandas.Series` 的数值判断重复项。

+ `FillNa(df: Union[pd.DataFrame, pd.Series], fval)`

  填充 `df` 数据对象中的空值，`fval` 可设置要填充的值。

+ `Url(column: Union[list, pd.Series, tuple])`

  检查 `column` 中的元素是否是一个 url 链接.

+ `RadioInput(column, lib)`

  选值匹配，根据 `lib` 中的标准选值及其别名对应关系检查 `column` 对象中的值是否标准，并尽力将其转换为标准值，无法自动转换的会执行手动对应引导。

### 具有值处理功能的映射模型定义

如同单纯的结构转换模型，带有值处理功能的数据模型也可以被定义为具备字段映射功能的数据模型，从而实现更广泛通用的数据处理能力：

```python
@imodel  
class SmartCleaner(Enum):  
    拉丁名 = BioName(['$scientificName', ('$genus', '$specificEpithet', '$taxonRank', '$infraspecificEpithet', ' ')], style='scientificName') 
    经度__纬度 = GeoCoordinate(('$decimalLatitude', '$decimalLongitude', ';')) 
    采集日期 = DateTime('$eventDate') 
    海拔__海拔高 = Number('$minimumElevationInMeters', '$maximumElevationInMeters', int) 
    国__省__市__县 = AdminDiv(('$country', '$province', '$city', '$county', ',')) 

```

输出：

```python
cleandata = SmartCleaner(r"/Users/.../dirtydata.xlsx", fields_mapping=True)
cleandata.df.head()                                                                                                                                                       
Out: 
             拉丁名           经度       纬度    采集日期    海拔  海拔高   国     省                 市      县
0 Trifolium repens L.      28.5746  99.8188    19780000  1400  1800  中国  河北省              承德市   None
1 Lauraceae                27.9167     99.6    19820824  1200  1300  中国  湖南省  湘西土家族苗族自治州   吉首市
2 Glycine max (L.) Merr.   38.5747  99.8342    19830500   400   600  中国  云南省    西双版纳傣族自治州   勐腊县
3 Glycine                  24.5976  100.081  !1983.6.31  1000  1100  中国  云南省       大理白族自治州   None
4 !Rubia cordifolia var. sylvatica 31.0701  96.9746 19820824  3800  3800  中国  四川省  甘孜藏族自治州   德格县
```

### 为模型自定义数据处理功能

`ipybd` 数据模型除了可以使用内置的值处理功能类，还同样支持将自定义的函数应用到 `ipybd` 模型之中。这里以上文清洗获得的 `cleandata` 数据集为例，`cleandata` 数据集中的海拔属性有两列数据，如果我们想在此基础上获得一个相对准确可用的物种空间位置数据集，就需要对 `cleandata` 的海拔区间进行处理，使其变成一个单值。最简单的方式就是获得每个物种记录的海拔区间平均值，那么我们就可以定义一个求平均数的函数：

```python
from ipybd import imodel, ifunc                                                                               from enum import Enum                                                                                                                                              
@ifunc 
def avg(min_alt, max_alt): 
    return (min_alt+max_alt)/2                                                                                                                                                                   
```

`ipybd` 提供了一个 `ifunc` 修饰符，它可以将用户自定义的函数转换为能够解析`ipybd` 模型参数语义的功能函数。如此，被修饰的函数不仅可以传递和使用普通的参数，还可以接收`$`修饰的数据对象（`pandas.Series`类型）。上方的 `avg` 函数经 `ifunc`修饰后，我们便可以向下方一样，在 `MyFuncModel` 模型中通过`$海拔低` `$海拔高` 这样的表达形式将原始数据集中与之对应的两列`pandas.Series` 对象传递给 `avg` 函数。

```python
@imodel 
class MyFuncModel(Enum): 
    拉丁名 = '$拉丁名' 
    经度 = '$经度' 
    纬度 = '$纬度' 
    海拔1 = '$海拔' 
    海拔2 = '$海拔高' 
    海拔 = avg('$海拔1', '$海拔2')   
    
    
mydata = MyFuncModel(cleandata.copy())  

mydata.df.head()

Out: 
                          拉丁名         经度          纬度      海拔
0               Trifolium repens L.  28.574633   99.818817  1600.0
1                         Lauraceae  27.916667   99.600000  1250.0
2            Glycine max (L.) Merr.  38.574683   99.834233   500.0
3                           Glycine  24.597561  100.081378  1050.0
4  !Rubia cordifolia var. sylvatica  31.070100   96.974600  3800.0

```

最终 `avg` 函数会返回求得的平均数，需要特别注意的是 `ipybd` 对于数据对象的接收和传递都是基于 `pandas.Series` 对象，因此用户自定义的函数处理数据的方式必须要能够适用于 `pandans.Series`对象，同时返回的数据对象也需要是`pd.Series` 类型（如果只是需要返回单个`pd.Series`对象，那也可以是`list` `dict` `ndarray`等可以生成`DataFrame`的类型）。`ipybd` 会自动将返回的结果拼接到新的数据集中，同时还会一并删除之前参与运算的数据对象以简化数据集。而如果函数最终需要返回多个数据对象，或者不想删除已参与运算的数据对象，那么在自定义函数时，就需要返回多个`pandas.Series` 对象以供`ipybd`将其重新整合到数据集中。比如对于上述 `avg` 函数，如果我们不仅想求得每个物种记录的平均海拔高度，还想保留原始海拔信息，就需要：

```python
@ifunc 
def avg(min_alt, max_alt): 
  	#将参与运算的 Series 对象一并返回，以避免其被删除
    return min_alt, max_alt, (min_alt+max_alt)/2 
                                                          
@imodel 
class MyFuncModel(Enum): 
    拉丁名 = '$拉丁名' 
    经度 = '$经度' 
    纬度 = '$纬度' 
    海拔1 = '$海拔' 
    海拔2 = '$海拔高' 
    #枚举元素的key也要写成多个字段名，以匹配 avg 的返回结果
    海拔低__海拔高__海拔 = avg('$海拔1', '$海拔2')
                                                                                                                                               
mydata = MyFuncModel(cleandata.copy())                                                                                                                 
mydata.df.head()                                                                                                                                                         
Out: 
                       拉丁名         经度          纬度     海拔低  海拔高    海拔
0               Trifolium repens L.  28.574633   99.818817  1400  1800  1600.0
1                         Lauraceae  27.916667   99.600000  1200  1300  1250.0
2            Glycine max (L.) Merr.  38.574683   99.834233   400   600   500.0
3                           Glycine  24.597561  100.081378  1000  1100  1050.0
4  !Rubia cordifolia var. sylvatica  31.070100   96.974600  3800  3800  3800.0
```

此外，`pandas.Series` 本身已经有很多成熟强大的[功能](https://pandas.pydata.org/pandas-docs/stable/search.html?q=pandas.Series#)可供直接调用，熟练掌握它也可以大幅简化自定义函数的功能实现难度。

## 五、DarwinCore 模型

`ipybd` 针对国内物种记录常见的使用常见，内置了一些具备字段映射功能的数据模型，这些模型主要基于 `DarwinCore` 标准定义，可以快速执行众源数据的清洗和转换。相应的模型包括：

**`Occurrence`**: 适用于标本、物种分布记录的整理；

**`CVH`**：适用于转数据集为CVH格式；

**`NSII`**：适用于转数据集为NSII格式；

**`KingdoniaPlant`**:适用于转数据集为 Kingdonia 植物标本数据导入格式；

**`NOIOccurrence`**：适用于转数据集为 noi.link 平台注册数据集；

使用这些模型，只需将数据对象直接传递给它即可：

```python
mycollection = Occurrence(your dataset object)
```