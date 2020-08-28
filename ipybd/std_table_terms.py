from enum import Enum
from ipybd.data_cleaner import *

'''定义的枚举将传递给 core.ReStructureTable 重构原始表格

    重构的表格，其列名将转换为枚举的 name, 枚举成员的值则定义了相应值的进一步处理方式

    枚举的 value 按序包含三个组成部分:校验功能、位置参数、数据列的数量；
    首个元素为值校验类，如果不需要效验，可为空；
    之后的参数为校值需要传递的一至多个位置参数，若校验类缺省，则值不做校验；位置参数必须
    由标准列名库中定义的列名作为参数；
    最后的参数用于标注位置参数中实际传递给校验功能的数据列数量，以让程序从参数中区分出哪
    些参数是实际的数据，以便在校验之前做必要的预处理。如下方的 individualCount 字段，
    虽然校值时，需要传递两个位置参数‘individualCount’和'int'，但只有individualCount 
    这个参数是数据表中真实有对应的数据列， 而 'int' 参数只是指示程序按照整型数字处理数
    据而已，因此其最后一个值设为 1。

    单个位置参数若需要先由多个标准字段合并而成，则使用 () 包裹这些字段，被 () 包裹的字
    段，最后一个值为合并后字段间的连接符，目前只支持使用相同的连接符连接不同字段；若最
    终希望将多列折叠为单列数据结构，则可设连接符为 'd', 'l', 'r', 'o', 'a'， 其分别对
    应者 ‘dict’，‘list’， ‘rowList’, 'jsonObject', 'jsonArray' 等形式。

    若某个位置参数可能存在多种形式，所有可能的形式需以 [] 包裹，如下方 scientificName。

    某些参数需要先由多个标准字段先进一步合并组成，而参与合并的字段在实际表中可能有多种处
    理方式，比如植物学名可能是（属名 种加词 种下 命名人）
    也能是（属名 种加词 种下等级 种下 命名人）学名中的 taxonRank 字段有可能就不是一个
    独立的字段，而是被归并到了 specificEpithet 内，类似这种多字段组合而成的位置参数，
    在定义时，应尽可能使用要素更全的表达式，程序会自动排除表达式中无法找到的字段，并利
    用找到的字段进行组装。

    以 _ 开头的枚举 name 属于临时列名，有些列可能需要多次处理，比如海拔，实际列可能是
    个区间，也可能只是个单值，定义 Enum 时可以先对海拔列尝试进行单值校验，并以 _ 列名
    临时性的标注列，然后再尝试对两列进行值区间判断。如果实际表格只是个单值，程序不会继
    续执行区间判断代码，此时被 _ 标注的相应列名会被去除 _ 作为转换后的正式列名，因此如
    果一列是否可拆具有不确定性，相关数值又需要分多步进行校验，则可以采用 _ + 正式列名的
    方式进行临时性的标注，这样即便后续处理实际不存在，也可以将正式列名赋予相应列。

'''


class OccurrenceTerms(Enum):
    # Record
    basisOfRecord = RadioInput, 'basisOfRecord', 'basisOfRecord', 1
    rights = 'rights', 1
    rightsHolder = 'rightsHolder', 1
    licence = 'licence', 1
    modified = DateTime, 'modified', 'datetime', 1
    references = 'references', 1
    institutionCode = RadioInput, 'institutionCode', 'institutionCode', 1
    classification = RadioInput, 'classification', 'classification', 1
    # Occurrence
    OccurrenceID = UniqueID, 'occurrenceID', 1
    catalogNumber = UniqueID, 'catalogNumber', 1
    otherCatalogNumbers = 'otherCatalogNumbers', 1
    preparations = RadioInput, 'preparations', 'preparations', 1
    disposition = RadioInput, 'disposition', 'disposition', 1
    preservedTime = DateTime, 'preservedTime', 'datetime', 1
    # 柜子位置自行在 std_options_alias 中定义
    preservedLocation = RadioInput, 'preservedLocation', 'preservedLocation', 1
    recordedBy = HumanName, 'recordedBy', 1
    recordNumber = 'recordNumber', 1
    individualCount = NumericalInterval, 'individualCount', None, 'int', 1
    lifeStage = RadioInput, 'lifeStage', 'lifeStage', 1
    sex = RadioInput, 'sex', 'sex', 1
    behavior = 'behavior', 1
    habit = RadioInput, 'habit', 'habit', 1
    establishmentMeans = RadioInput, 'establishmentMeans', 'establishmentMeans', 1
    molecularMaterialSample = RadioInput, 'molecularMaterialSample', 'molecularMaterialSample', 1
    # Event
    eventDate = DateTime, 'eventDate', 1
    habitat = 'habitat', 1
    samplingProtocol = RadioInput, 'samplingProtocol', 'samplingProtocol', 1
    fieldNumber = 'fieldNumber', 1
    fieldNotes = 'fieldNotes', 1
    fundedBy = 'fundedBy', 1
    # Location
    country = AdminDiv, ('country', 'province', 'city', 'county', '::'), 1
    province = AdminDiv, ('country', 'province', 'city', 'county', '::'), 1
    city = AdminDiv, ('country', 'province', 'city', 'county', '::'), 1
    county = AdminDiv, ('country', 'province', 'city', 'county', '::'), 1
    locality = ('locality', 'mountain', 'waterBody', ','), 1
    decimalLatitude = GeoCoordinate, ('decimalLatitude', 'decimalLongitude', ';'), 1
    decimalLongitude = GeoCoordinate, ('decimalLatitude', 'decimalLongitude', ';'), 1
    _minimumElevationInMeters = NumericalInterval, 'minimumElevationInMeters', 1
    _maximumElevationInMeters = NumericalInterval, 'maximumElevationInMeters', 1
    minimumElevationInMeters = NumericalInterval, '_minimumElevationInMeters', '_maximumElevationInMeters', 2
    maximumElevationInMeters = NumericalInterval, '_minimumElevationInMeters', '_maximumElevationInMeters', 2
    _minimumDepthInMeters = NumericalInterval, 'minimumDepthInMeters', 1
    _maximumDepthInMeters = NumericalInterval, 'maximumDepthInMeters', 1
    minimumDepthInMeters = NumericalInterval, '_minimumDepthInMeters', '_maximumDepthInMeters', 2
    maximumDepthInMeters = NumericalInterval, '_minimumDepthInMeters', '_maximumDepthInMeters', 2
    associatedMedia = 'associatedMedia', 1
    associatedReferences = 'associatedReferences', 1
    associatedSequences = 'associatedSequences', 1
    occurrenceRemarks = 'occurrenceRemarks', 1
    # Taxon
    kingdom = 'kingdom', 1
    phylum = 'phylum', 1
    _class  = 'class', 1
    order = 'order', 1
    family = 'family', 1
    vernacularName = 'vernacularName', 1
    # Identification
    scientificName = BioName, [('genus', 'specificEpithet', 'specificEpithetAuthorShip', 'taxonRank', 'infraspecificEpithet', 'scientificNameAuthorship', ' '), 'scientificName'], 1
    typeStatus = RadioInput, 'typeStatus', 'typeStatus', 1
    identifiedBy = HumanName, 'identifiedBy', 1
    dateIdentified = DateTime, 'dateIdentified', 1
    identificationRemarks = 'identificationRemarks', 1
    # Organism of Plant
    root = 'root', 1
    stem = 'stem', 1
    leaf = 'leaf', 1
    flower = 'flower', 1
    fruit = 'fruit', 1
    seed = 'seed', 1
    # Organism of Aves
    weightInGrams = NumericalInterval, 'weightInGrams', 1
    bodyLengthInMillimeters = NumericalInterval, 'bodyLengthInMillimeters', 1
    wingChordInMillimeters = NumericalInterval, 'wingLengthInMillimeters', 1
    tailLengthInMillimeters = NumericalInterval, 'tailLengthInMillimeters', 1
    tarsusInMillimeters = NumericalInterval, 'tarsusInMillimeters', 1
    exposedCulmenInMillimeters = NumericalInterval, 'exposedCulmenInMillimeters', 1
    irisColor = 'irisColor', 1
    billColor = 'billColor', 1
    legsColor = 'legsColor', 1
    fat = RadioInput, 'fat', 'fat', 1
    heightOfNestInMeters = NumericalInterval, 'heightOfNestInMeters', 1
    substrateOfNest = 'substrateOfNest', 1
    constructionOfNest = 'constructionOfNest', 1
    numOfEggsTaken = NumericalInterval, 'numOfEggsTaken', None, 'int', 1
    incubation = 'incubation', 1
    organismRemarks = 'organismRemarks', 1


class KingdoniaPlantTerms(Enum):
    catalogNumber = UniqueID, 'catalogNumber', 1
    institutionCode = RadioInput, 'institutionCode', 'institutionCode', 1
    otherCatalogNumbers = 'otherCatalogNumbers', 1
    classification = RadioInput, 'classification', 'classification', 1
    lifeStage = RadioInput, 'lifeStage', 'lifeStage', 1
    disposition = RadioInput, 'disposition', 'disposition', 1
    preservedLocation = RadioInput, 'preservedLocation', 'preservedLocation', 1
    preservedTime = DateTime, 'preservedTime', 'datetime', 1
    recordedBy = HumanName, 'recordedBy', 1
    recordNumber = 'recordNumber', 1
    eventDate = DateTime, 'eventDate', 'datetime', 1
    individualCount = NumericalInterval, 'individualCount', None, 'int', 1
    country = AdminDiv, ('country', 'province', 'city', 'county', '::'), 1
    province = AdminDiv, ('country', 'province', 'city', 'county', '::'), 1
    city = AdminDiv, ('country', 'province', 'city', 'county', '::'), 1
    county = AdminDiv, ('country', 'province', 'city', 'county', '::'), 1
    locality = ('locality', 'mountain', 'waterBody', ','), 1
    habitat = 'habitat', 1
    habit = RadioInput, 'habit', 'habit', 1
    decimalLatitude = GeoCoordinate, ('decimalLatitude', 'decimalLongitude', ';'), 1
    decimalLongitude = GeoCoordinate, ('decimalLatitude', 'decimalLongitude', ';'), 1
    _minimumElevationInMeters = NumericalInterval, 'minimumElevationInMeters', 1
    _maximumElevationInMeters = NumericalInterval, 'maximumElevationInMeters', 1
    minimumElevationInMeters = NumericalInterval, '_minimumElevationInMeters', '_maximumElevationInMeters', 2
    maximumElevationInMeters = NumericalInterval, '_minimumElevationInMeters', '_maximumElevationInMeters', 2
    occurrenceRemarks = 'occurrenceRemarks', 1
    _scientificName = BioName, [('genus', 'specificEpithet', 'specificEpithetAuthorShip', 'taxonRank', 'infraspecificEpithet', 'scientificNameAuthorship', ' '), 'scientificName'], 1
    scientificName = FillNa, '_scientificName', 'unknown', 1
    _typeStatus = RadioInput, 'typeStatus', 'typeStatus', 1
    typeStatus = FillNa, '_typeStatus', 'not type', 1
    _identifiedBy = HumanName, 'identifiedBy', 1
    identifiedBy = FillNa, '_identifiedBy', '无', 1
    _dateIdentified = DateTime, 'dateIdentified', 'datetime', 1
    dateIdentified = FillNa, '_dateIdentified', '0000:00:00 00:00:02', 1
    _identifiedByID = UniqueID, 'identifiedByID', 1
    identifiedByID = FillNa, '_identifiedByID', '0', 1
    identifications = ("scientificName", "identifiedByID", "identifiedBy",  "dateIdentified", "typeStatus", "l"), 1
    花 = 'flower', 1
    叶 = 'leaf', 1
    茎 = 'stem', 1
    果实 = 'fruit', 1
    种子 = 'seed', 1
    根 =  'root', 1
    不定根 = 'rhizoids', 1
    #孢子囊（群）= '孢子囊（群）', 1
    #孢子叶（球）= '孢子叶（球）', 1
    频度 = RadioInput, 'frequency', 1
    胸径 = NumericalInterval, 'DBH', 1
    体高 = 'height', 1
    野外鉴定 = '野外鉴定', 1
    当地名称 = 'vernacularName', 1
    dynamicProperties = ('频度', '胸径', '体高', '孢子囊（群）', '孢子叶（球）', '花', '叶', '茎', '果实', '种子', '根', '不定根', '野外鉴定', '当地名称', 'o'), 1
    organismRemarks = 'organismRemarks', 1
    associatedMedia = 'associatedMedia', 1
    _molecularMaterialSample = RadioInput, 'molecularMaterialSample', 'molecularMaterialSample', 1
    molecularMaterialSample = FillNa, '_molecularMaterialSample', '无', 1
    _seedMaterialSample = NumericalInterval, 'seedMaterialSample', None, 'int', 1
    seedMaterialSample = FillNa, '_seedMaterialSample', '0', 1
    _livingMaterialSample = NumericalInterval, 'livingMaterialSample', None, 'int', 1
    livingMaterialSample = FillNa, '_livingMaterialSample', '0', 1
    MaterialSample = ('molecularMaterialSample', 'seedMaterialSample', 'livingMaterialSample', 'o'), 1


class KingdoniaAvesTerms(Enum):
    pass
