[![docsc - readthedocs](https://img.shields.io/badge/docs-passing-brightgreen?style=flat)](https://ipybd.readthedocs.io) [![social - wechat](https://img.shields.io/badge/%E5%85%AC%E4%BC%97%E5%8F%B7-%E4%B8%9C%E9%A3%8E%E7%9A%84%E5%B0%8F%E9%99%A2-brightgreen?style=flat&logo=weChat)](http://mp.weixin.qq.com/s?__biz=Mzg2MTczOTQ5Mg==&mid=2247483662&idx=1&sn=fa2fe5741b0320773a596f3b3e7f9533&chksm=ce13c185f9644893c21090a87338ccee50a28ef75f62113733513698ac663cfc44ed8ee0f5c2&scene=18#wechat_redirect) ![GitHub - commits](https://badgen.net/github/commits/leisux/ipybd) [![Downloads](https://static.pepy.tech/badge/ipybd/week)](https://pepy.tech/project/ipybd) [![Downloads](https://static.pepy.tech/badge/ipybd/month)](https://pepy.tech/project/ipybd) [![Downloads](https://static.pepy.tech/badge/ipybd)](https://pepy.tech/project/ipybd) ![PyPI - License](https://img.shields.io/pypi/l/ipybd?color=red)

`ipybd` 是一款由 `Python` 开发的中文生物多样性数据清洗、统计与分析框架，详细的使用请见[文档](https://ipybd.readthedocs.io)。当前的 `ipybd` 版本实现了一个**通用**的生物多样性数据整合框架，它可以显著提升数据平台、数据管理机构、数据使用者对不同来源、不同格式、不同品质、不同规范的数据集进行统一的**批量化**清洗转换与整合利用的能力，从而大幅降低数据处理的门槛和成本，提高数据分析前的数据处理品质和效率。目前 `ipybd` 已经具备了以下一些能力：

+ **数据装载**：目前支持从Excel/CSV/TEXT/JSON/Pandas.DataFrame 以及各类关系型数据库（比如Mysql）导入数据；

+ **物种学名**：能够将各种手写的拉丁名转化为规范的学名格式，并可以在线批量获取 [POWO](http://www.plantsoftheworldonline.org/), [IPNI](https://www.ipni.org/), [中国生物物种名录](http://www.sp2000.org.cn/), [Tropicos](https://www.tropicos.org)上相应物种的最新分类阶元、分类处理、物种图片、发表文献、相关异名等信息；

+ **日期与时间**：可以对各类手工转录的日期和时间，进行严格的校验、清洗和转换，并可根据需要输出不同样式；

+ **经纬度**：可以对各类手工转录的经纬度，进行严格的清洗、校验和转换；

+ **中文行政区划**：可以对各种自然语言表达的中文县级及其以上的行政区划进行高品质的匹配、校正和转换；

+ **选值**：能够自定义各种字段的选值和转换关系，并根据转换关系，自动完成现有值的规范化；

+ **数值和数值区间**：可以对各类数值或数值区间，进行自动化的清洗、校正和转换；

+ **拆分与合并**：`ipybd` 不仅可以对数据列进行各种合并和拆分，还可以将单列、多列或整个表格的数据列映射为各类 Python `dict` `list` 对象或者 JSON `Object` 和 `Array`，从而为各种数据分析和互联网平台的数据交换工作提供灵活的格式转换支持。

+ **标签打印**：能够生成带有条形码样式的标签文档以供打印。

+ **数据输出**：经过处理的数据，可以输出为Excel/CSV文件或者直接更新至相应的数据库之中。

`ipybd` 定义了一套简洁的语义，可以帮助用户快速的定制出个性化的数据转换模型。这些模型能够根据相应任务的需要，将以上各种数据处理能力自由拼接和组合，以实现数据集的自动化清洗和转换。

## 特别声明

1. iPybd 遵从 GNU General Public License v3.0 许可，© 徐洲锋-中国科学院华南植物园。
2. 本项目的顺利开展受到了中国科学院华南植物园（SCBG）、中国国家标本资源平台（nsii.org.cn）支持

