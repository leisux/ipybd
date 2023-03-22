[![Documentation Status](https://readthedocs.org/projects/ipybd/badge/?version=latest)](https://ipybd.readthedocs.io/zh_CN/latest/?badge=latest) [![social - wechat](https://img.shields.io/badge/%E5%85%AC%E4%BC%97%E5%8F%B7-%E4%B8%9C%E9%A3%8E%E7%9A%84%E5%B0%8F%E9%99%A2-brightgreen?style=flat&logo=weChat)](http://mp.weixin.qq.com/s?__biz=Mzg2MTczOTQ5Mg==&mid=2247483843&idx=1&sn=836c7c35a3dddf9e30c6546ce6e2b6f3&chksm=ce13c148f964485e1f4da455dd02f698d9bda84440ce9ce5b17a05e1bea24759acd10551a0f0#wechat_redirect) [![Downloads](https://static.pepy.tech/badge/ipybd/week)](https://pepy.tech/project/ipybd) [![Downloads](https://static.pepy.tech/badge/ipybd/month)](https://pepy.tech/project/ipybd) [![Downloads](https://static.pepy.tech/badge/ipybd)](https://pepy.tech/project/ipybd) ![PyPI - License](https://img.shields.io/pypi/l/ipybd?color=red)

`ipybd` 是一款由 `Python` 开发的中文生物多样性数据清洗、统计与分析框架。当前的 `ipybd` 版本实现了一个**通用**的生物多样性数据整合框架，它可以实现对不同来源、不同格式、不同品质、不同规范的数据集进行统一的**批量化**清洗转换与整合，进而大幅降低数据处理的门槛和成本，提高数据分析前的数据处理品质和效率。安装和使用说明请见[文档](https://ipybd.readthedocs.io)。

### 一、主要功能

目前 `ipybd` 已经具备了以下一些能力：

**数据装载**：目前支持从Excel/CSV/TEXT/JSON/Pandas.DataFrame 以及各类关系型数据库（比如Mysql）导入数据。

**物种学名**：能够对拉丁学名进行各种拆分和合并，并可以在线批量获取 [POWO](http://www.plantsoftheworldonline.org/)，[IPNI](https://www.ipni.org/)，[中国生物物种名录](http://www.sp2000.org.cn/)，[Tropicos](https://www.tropicos.org) 上相应物种的最新分类阶元、分类处理、物种图片、发表文献、相关异名等信息。

**日期与时间**：可以对各类手工转录的日期和时间，进行严格的校验、清洗和转换，并可根据需要输出不同样式。

**经纬度**：可以对各类手工转录的经纬度，进行严格的清洗、校验和转换。

**中文行政区划**：可以对各种自然语言表达的中文县级及其以上的行政区划进行高品质的匹配、校正和转换。

**选值**：能够自定义各种字段的选值和转换关系，并根据转换关系，自动完成现有值的规范化。

**数值和数值区间**：可以对各类数值或数值区间，进行自动化的清洗、校正和转换。

**拆分与合并**：`ipybd` 可以对数据列进行各种合并和拆分，可以将单列、多列或整个表格的数据列映射为各类 Python `dict` `list` 对象或者 JSON `Object` 和 `Array`，从而为各种数据分析和互联网平台的数据交换工作提供灵活的格式转换支持。

**标签打印**：能够生成有条形码或者无条形码的标签文档以供打印。

**数据模型**：`ipybd` 定义了一套简洁的语义，可以帮助用户快速的定制出个性化的数据转换模型。这些模型能够根据相应任务的需要，将以上各种数据处理能力（或者用自定义的功能）自由拼接和组合，以实现数据集的自动化清洗和转换。

**数据输出**：经过处理的数据，支持输出为Excel/CSV文件或者直接更新到数据库。

### 二、文献引用
徐洲锋. iPybd[CP]. 广州: 中国科学院华南植物园, 2023.https://github.com/leisux/ipybd

Xu Zhoufeng(2023). iPybd: A Powerful Data Cleaner For Biodiversity. South China National Botanical Garden, Guangzhou, China. 
https://github.com/leisux/ipybd

### 三、特别感谢
本库的顺利开发受到了中国科学院华南植物园（SCBG）、中国国家标本资源平台（nsii.org.cn）的支持。

