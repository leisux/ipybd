# ipybd

### 程序功能和用途

ipybd 是一款生物多样性数据清洗、统计与分析程序包，ipybd 当前版本已经实现了完整的数据 ETL 流程,可以大幅提高数据整理、清洗、整合的效率和品质：

1. 可以通过生物物种的中文和拉丁名，批量获取 sp2000.0rg.cn, ipni.org, powo 上相应学名的最新分类学处理；
2. 可对各类手工转录的经纬度、中文行政区划、人名、拉丁学名、日期与时间、各类点选值（如植物习性）、各类数值/数值区间（如海拔）进行自动化的清洗、校正和转换；
3. 可将绝大多数的生物多样性 Excel 数据表转换为遵从 DWC 标准的规范数据表，实现众源数据的高效 ETL；
4. 可以快速定制特定的数据模板，实现众源数据到该数据模板的转换；
5. 可自动识别植物标本图片的条形码，并以此重命名该图片文件名，该功能可以大大节约标本数字化时植物标本影像的命名工作效率；


### 安装方法

ipybd 已经上传到 pypy，你可以在你的本机 python 环境中安装 ipybd：

```
pip install ipybd
```
### 使用方法

#### 生物物种发生记录的标准化转换
```
from ipybd import OccurrenceRecord as ocr
```
### 物种名称处理
```
from ipybd import BioName
```
### 数据表的各种拆分和合并
```
from ipybd import FormatTable as ft
```
### 中文行政区划清洗和转换
```
from ipybd import AdminDiv
```
### 日期和时间清洗和转换
```
from ipybd import DateTime
```
### 经纬度清洗和转换
```
from ipybd import GeoCoordinate
```
### 数值及数值区间的清洗和转换
```
from ipybd import NumericalInterval
```
### 重复值标注
```
from ipybd import UniqueID
```
### 数据转换模板的定制
```
from ipybd import RestructureTable as rt
```

### 特别声明

1. ipybd 遵从 GNU General Public License v3.0 许可    
2. 本软件由 NSII 项目资助，中国科学院昆明植物研究所标本馆（KUN）开发
