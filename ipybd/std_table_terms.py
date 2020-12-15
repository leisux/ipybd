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

class CvhTerms(Enum):
    条形码 = UniqueID('>catalogNumber')
    馆代码 = RadioInput('>institutionCode', 'institutionCode')
    流水号 = '>otherCatalogNumbers'
    标本状态 = RadioInput('>lifeStage', 'lifeStage')
    库存 = RadioInput('>disposition', 'disposition')
    采集人 = HumanName('>recordedBy')
    采集号 = '>recordNumber'
    份数 = Number('>individualCount', None, int)
    采集日期 = DateTime('>eventDate')
    国家 = AdminDiv(('>country', '>province', '>city', '>county', '::'))
    province = AdminDiv(('>country', '>province', '>city', '>county', '::'))
    city = AdminDiv(('>country', '>province', '>city', '>county', '::'))
    区县 = AdminDiv(('>country', '>province', '>city', '>county', '::'))
    省市 = ('>province', '>city', ',')
    小地点 = ('>locality', '>mountain', '>waterBody', ',')
    纬度 = GeoCoordinate(('>decimalLatitude', '>decimalLongitude', ';'))
    经度 = GeoCoordinate(('>decimalLatitude', '>decimalLongitude', ';'))
    _minimumElevationInMeters = Number('>minimumElevationInMeters')
    _maximumElevationInMeters = Number('>maximumElevationInMeters')
    海拔 = Number('>minimumElevationInMeters', '>maximumElevationInMeters')
    海拔高 = Number('>minimumElevationInMeters', '>maximumElevationInMeters')
    生境 = '>habitat'
    习性 = RadioInput('>habit', 'habit')
    备注 = '>occurrenceRemarks'
    中文名 = '>vernacularName'
    科 = '>family'
    拉丁名 = BioName(['>scientificName', ('>genus', '>specificEpithet', '>specificAuthorship', '>taxonRank', '>infraspecificEpithet', '>scientificNameAuthorship', ' ')])
    模式类型 = RadioInput('>typeStatus', 'typeStatus')
    鉴定人 = HumanName('>identifiedBy')
    鉴定日期 = DateTime('>dateIdentified')



class OccurrenceTerms(Enum):
    # Record
    basisOfRecord = RadioInput('>basisOfRecord', 'basisOfRecord')
    rights = '>rights'
    rightsHolder = '>rightsHolder'
    licence = '>licence'
    modified = DateTime('>modified', 'datetime')
    references = '>references'
    institutionCode = RadioInput('>institutionCode', 'institutionCode')
    classification = RadioInput('>classification', 'classification')
    # Occurrence
    OccurrenceID = UniqueID('>occurrenceID')
    catalogNumber = UniqueID('>catalogNumber')
    otherCatalogNumbers = '>otherCatalogNumbers'
    preparations = RadioInput('>preparations', 'preparations')
    disposition = RadioInput('>disposition', 'disposition')
    preservedTime = DateTime('>preservedTime', 'datetime')
    # 柜子位置自行在 std_options_alias 中定义
    preservedLocation = RadioInput('>preservedLocation', 'preservedLocation')
    recordedBy = HumanName('>recordedBy')
    recordNumber = '>recordNumber'
    individualCount = Number('>individualCount', None, int)
    lifeStage = RadioInput('>lifeStage', 'lifeStage')
    sex = RadioInput('>sex', 'sex')
    behavior = '>behavior'
    habit = RadioInput('>habit', 'habit')
    establishmentMeans = RadioInput('>establishmentMeans', 'establishmentMeans')
    molecularMaterialSample = RadioInput('>molecularMaterialSample', 'molecularMaterialSample')
    # Event
    eventDate = DateTime('>eventDate')
    habitat = '>habitat'
    samplingProtocol = RadioInput('>samplingProtocol', 'samplingProtocol')
    fieldNumber = '>fieldNumber'
    fieldNotes = '>fieldNotes'
    fundedBy = '>fundedBy'
    # Location
    country = AdminDiv(('>country', '>province', '>city', '>county', '::'))
    province = AdminDiv(('>country', '>province', '>city', '>county', '::'))
    city = AdminDiv(('>country', '>province', '>city', '>county', '::'))
    county = AdminDiv(('>country', '>province', '>city', '>county', '::'))
    locality = ('>locality', '>mountain', '>waterBody', ',')
    decimalLatitude = GeoCoordinate(('>decimalLatitude', '>decimalLongitude', ';'))
    decimalLongitude = GeoCoordinate(('>decimalLatitude', '>decimalLongitude', ';'))
    _minimumElevationInMeters = Number('>minimumElevationInMeters')
    _maximumElevationInMeters = Number('>maximumElevationInMeters')
    minimumElevationInMeters = Number('>minimumElevationInMeters', '>maximumElevationInMeters')
    maximumElevationInMeters = Number('>minimumElevationInMeters', '>maximumElevationInMeters')
    _minimumDepthInMeters = Number('>minimumDepthInMeters')
    _maximumDepthInMeters = Number('>maximumDepthInMeters')
    minimumDepthInMeters = Number('>minimumDepthInMeters', '>maximumDepthInMeters')
    maximumDepthInMeters = Number('>minimumDepthInMeters', '>maximumDepthInMeters')
    associatedMedia = '>associatedMedia'
    associatedReferences = '>associatedReferences'
    associatedSequences = '>associatedSequences'
    occurrenceRemarks = '>occurrenceRemarks'
    # Taxon
    kingdom = '>kingdom'
    phylum = '>phylum'
    _class  = '>class'
    order = '>order'
    family = '>family'
    vernacularName = '>vernacularName'
    # Identification
    scientificName = BioName(['>scientificName', ('>genus', '>specificEpithet', '>specificAuthorship', '>taxonRank', '>infraspecificEpithet', '>scientificNameAuthorship', ' ')])
    typeStatus = RadioInput('>typeStatus', 'typeStatus')
    identifiedBy = HumanName('>identifiedBy')
    dateIdentified = DateTime('>dateIdentified')
    identificationRemarks = '>identificationRemarks'
    # Organism of Plant
    root = '>root'
    stem = '>stem'
    leaf = '>leaf'
    flower = '>flower'
    fruit = '>fruit'
    seed = '>seed'
    # Organism of Aves
    weightInGrams = Number('>weightInGrams')
    bodyLengthInMillimeters = Number('>bodyLengthInMillimeters')
    wingChordInMillimeters = Number('>wingLengthInMillimeters')
    tailLengthInMillimeters = Number('>tailLengthInMillimeters')
    tarsusInMillimeters = Number('>tarsusInMillimeters')
    exposedCulmenInMillimeters = Number('>exposedCulmenInMillimeters')
    irisColor = '>irisColor'
    billColor = '>billColor'
    legsColor = '>legsColor'
    fat = RadioInput('>fat', 'fat')
    heightOfNestInMeters = Number('>heightOfNestInMeters')
    substrateOfNest = '>substrateOfNest'
    constructionOfNest = '>constructionOfNest'
    numOfEggsTaken = Number('>numOfEggsTaken', None, int)
    incubation = '>incubation'
    organismRemarks = '>organismRemarks'


class NoiOccurrenceTerms(Enum):
    # Occurrence Object
    occurrenceID = UniqueID('>occurrenceID')
    catalogNumber = UniqueID('>catalogNumber')
    otherCatalogNumbers = '>otherCatalogNumbers'
    recordedBy = HumanName('>recordedBy')
    recordNumber = '>recordNumber'
    individualCount = Number('>individualCount', None, int)
    sex = RadioInput('>sex', 'sex')
    lifeStage = RadioInput('>lifeStage', 'lifeStage')
    behavior = '>behavior'
    establismentMeans = RadioInput('>establismentMeans', 'establismentMeans')
    preparations = RadioInput('>preparations', 'preparations')
    disposition = RadioInput('>disposition', 'disposition')
    associatedMedia = Url('>associatedMedia')
    associatedReferences = Url('>assocatedReferences')
    associatedSequences = Url('>associatedSequences')
    occurrenceRemarks = '>occurrenceRemarks'
    Occurrence = ('>occurrenceID', '>catalogNumber', '>otherCatalogNumbers', '>recordedBy', '>recordNumber', '>individualCount', '>sex', '>lifeStage', '>behavior', '>establishmentMeans', '>preparations', '>disposition', '>associatedMedia', '>associatedSequences', '>assocatedReferences', '>occurrenceRemarks', 'd')

    # Event Object
    eventDate = DateTime('>eventDate', 'utc')
    habitat = '>habitat'
    fieldNumber = '>fieldNumber'
    samplingProtocol = '>samplingProtocol'
    fieldNotes = '>fieldNotes'
    fundedBy = '>fundedBy'
    Event = ('>eventDate', '>habitat', '>fieldNumber', '>samplingProtocol', '>fieldNotes', '>fundedBy', 'd')

    # Location Object
    countryCode = '>countryCode'
    country = AdminDiv(('>country', '>province', '>city', '>county', '::'))
    province = AdminDiv(('>country', '>province', '>city', '>county', '::'))
    city = AdminDiv(('>country', '>province', '>city', '>county', '::'))
    county = AdminDiv(('>country', '>province', '>city', '>county', '::'))
    locality = ('>locality', '>mountain', '>waterBody', ',')
    decimalLatitude = GeoCoordinate(('>decimalLatitude', '>decimalLongitude', ';'))
    decimalLongitude = GeoCoordinate(('>decimalLatitude', '>decimalLongitude', ';'))
    _minimumElevationInMeters = Number('>minimumElevationInMeters')
    _maximumElevationInMeters = Number('>maximumElevationInMeters')
    minimumElevationInMeters = Number('>minimumElevationInMeters', '>maximumElevationInMeters')
    maximumElevationInMeters = Number('>minimumElevationInMeters', '>maximumElevationInMeters')
    geodeticDatum = RadioInput(">geodeticDatum", "geodeticDatum")
    _minimumDepthInMeters = Number('>minimumDepthInMeters')
    _maximumDepthInMeters = Number('>maximumDepthInMeters')
    minimumDepthInMeters = Number('>minimumDepthInMeters', '>maximumDepthInMeters')
    maximumDepthInMeters = Number('>minimumDepthInMeters', '>maximumDepthInMeters')
    _minimumDistanceAboveSurfaceInMeters = Number('>minimumDistanceAboveSurfaceInMeters')
    _maximumDistanceAboveSurfaceInMeters = Number('>maximumDistanceAboveSurfaceInMeters')
    minimumDistanceAboveSurfaceInMeters = Number('>minimumDistanceAboveSurfaceInMeters', '>maximumDistanceAboveSurfaceInMeters')
    maximumDistanceAboveSurfaceInMeters = Number('>minimumDistanceAboveSurfaceInMeters', '>maximumDistanceAboveSurfaceInMeters')
    Location = ('>countryCode', '>country', '>province', '>city', '>county', '>locality', '>decimalLatitude', '>decimalLongitude', '>minimumElevationInMeters', '>maximumElevationInMeters', '>minimumDepthInMeters', '>maximumDepthInMeters', '>minimumDistanceAboveSurfaceInMeters', '>maximumDistanceAboveSurfaceInMeters', 'd')

    # Idnetification Object
    vernacularName = '>vernacularName'
    scientificName = BioName(['>scientificName', ('>genus', '>specificEpithet', '>specificAuthorship', '>taxonRank', '>infraspecificEpithet', '>scientificNameAuthorship', ' ')])
    identifiedBy = HumanName('>identifiedBy')
    dateIdentified = DateTime('>dateIdentified', 'utc')
    typeStatus = RadioInput('>typeStatus', 'typeStatus')
    _Identification = ('>vernacularName', '>scientificName', '>identifiedBy', '>dateIdentified', '>typeStatus', 'd')
    Identification = ('>Identification', 'l')

    # Record Object
    institutionCode = RadioInput('>institutionCode', 'institutionCode')
    category = RadioInput('>category', 'category')
    basisOfRecord = RadioInput('>basisOfRecord', 'basisOfRecord')
    rights = '>rights'
    rightsHolder = '>rightsHolder'
    references = '>references'
    dataApi = '>dataApi'
    thumbnails = '>thumbnails'
    licence = '>licence'
    modified = DateTime('>modified', 'utc')
    Record = ('>institutionCode', '>category', '>basisOfRecord', '>rights', '>rightsHolder', '>references', '>dataApi', '>thumbnails', '>licence', '>modified', 'd')
    DictForNoiOccurrence = ('>Occurrence', '>Location', '>Identification', '>Event', '>Record', 'd')


class KingdoniaPlantTerms(Enum):
    catalogNumber = UniqueID('>catalogNumber')
    institutionCode = RadioInput('>institutionCode', 'institutionCode')
    otherCatalogNumbers = '>otherCatalogNumbers'
    classification = RadioInput('>classification', 'classification')
    lifeStage = RadioInput('>lifeStage', 'lifeStage')
    disposition = RadioInput('>disposition', 'disposition')
    preservedLocation = RadioInput('>preservedLocation', 'preservedLocation')
    preservedTime = DateTime('>preservedTime', 'utc')
    recordedBy = HumanName('>recordedBy')
    recordNumber = '>recordNumber'
    eventDate = DateTime('>eventDate', 'datetime')
    _individualCount = Number('>individualCount', None, int)
    individualCount = FillNa('>individualCount', 0)
    country = AdminDiv(('>country', '>province', '>city', '>county', '::'))
    stateProvince = AdminDiv(('>country', '>province', '>city', '>county', '::'))
    city = AdminDiv(('>country', '>province', '>city', '>county', '::'))
    county = AdminDiv(('>country', '>province', '>city', '>county', '::'))
    locality = ('>locality', '>mountain', '>waterBody', '>,')
    habitat = '>habitat'
    habit = RadioInput('>habit', 'habit')
    decimalLatitude = GeoCoordinate(('>decimalLatitude', '>decimalLongitude', ';'))
    decimalLongitude = GeoCoordinate(('>decimalLatitude', '>decimalLongitude', ';'))
    _minimumElevationInMeters = Number('>minimumElevationInMeters')
    _maximumElevationInMeters = Number('>maximumElevationInMeters')
    minimumElevationInMeters = Number('>minimumElevationInMeters', '>maximumElevationInMeters')
    maximumElevationInMeters = Number('>minimumElevationInMeters', '>maximumElevationInMeters')
    occurrenceRemarks = '>occurrenceRemarks'
    _scientificName = BioName(['>scientificName', ('>genus', '>specificEpithet', '>specificAuthorship', '>taxonRank', '>infraspecificEpithet', '>scientificNameAuthorship', ' ')])
    scientificName = FillNa('>scientificName', 'unknown')
    _typeStatus = RadioInput('>typeStatus', 'typeStatus')
    typeStatus = FillNa('>typeStatus', 'not type')
    _identifiedBy = HumanName('>identifiedBy')
    identifiedBy = FillNa('>identifiedBy', '无')
    _dateIdentified = DateTime('>dateIdentified', 'datetime')
    dateIdentified = FillNa('>dateIdentified', '0000:00:00 00:00:02')
    _identifiedByID = UniqueID('>identifiedByID')
    identifiedByID = FillNa('>identifiedByID', '0')
    _identifications = (">scientificName", ">identifiedByID", ">identifiedBy",  ">dateIdentified", ">typeStatus", "l")
    identifications = ('>identifications', 'l')
    花 = '>flower'
    叶 = '>leaf'
    茎 = '>stem'
    果实 = '>fruit'
    种子 = '>seed'
    根 = '>root'
    不定根 = '>rhizoids'
    #孢子囊（群）= '>孢子囊（群）')
    #孢子叶（球）= '>孢子叶（球）')
    频度 = RadioInput('>frequency', 'frequency')
    胸径 = Number('>DBH')
    体高 = '>height'
    野外鉴定 = '>temporaryIdentification'
    当地名称 = '>dialectName'
    dynamicProperties = ('>频度', '>胸径', '>体高', '>孢子囊（群）', '>孢子叶（球）', '>花', '>叶', '>茎', '>果实', '>种子', '>根', '>不定根', '>野外鉴定', '>当地名称', 'o')
    organismRemarks = '>organismRemarks'
    associatedMedia = '>associatedMedia'
    _molecularMaterialSample = RadioInput('>molecularMaterialSample', 'molecularMaterialSample')
    molecularMaterialSample = FillNa('>molecularMaterialSample', '无')
    _seedMaterialSample = Number('>seedMaterialSample', None, int)
    seedMaterialSample = FillNa('>seedMaterialSample', 0)
    _livingMaterialSample = Number('>livingMaterialSample', None, int)
    livingMaterialSample = FillNa('>livingMaterialSample', 0)
    MaterialSample = ('>molecularMaterialSample', '>seedMaterialSample', '>livingMaterialSample', 'o')


class KingdoniaAvesTerms(Enum):
    pass


class HerbLabelTerms(Enum):
    title = '>institutionName'
    titleNote = '>institutionCode'
    subTitle = '>fundedBy'
    family = '>family'
    vernacularName = '>vernacularName'
    genus = '>genus'
    specificEpithet = '>specificEpithet'
    specificAuthorship = '>specificAuthorship'
    taxonRank = '>taxonRank'
    infraspecificEpithet = '>infraspecificEpithet'
    scientificNameAuthorship = '>scientificNameAuthorship'
    scientificName = BioName('>scientificName')
    identifiedBy = HumanName('>identifiedBy')
    dateIdentified = DateTime('>dateIdentified', 'date')
    country = AdminDiv(('>country', '>province', '>city', '>county', '::'))
    province = AdminDiv(('>country', '>province', '>city', '>county', '::'))
    city = AdminDiv(('>country', '>province', '>city', '>county', '::'))
    county = AdminDiv(('>country', '>province', '>city', '>county', '::'))
    locality = ('>locality', '>mountain', '>waterBody', ',')
    habitat = '>habitat'
    individualCount = Number('>individualCount', None, int)
    habit = RadioInput('>habit', 'habit')
    flower = '>flower'
    leaf = '>leaf'
    stem = '>stem'
    fruit = '>fruit'
    seed = '>seed'
    root = '>root'
    rhizoids = '>rhizoids'
    # 孢子囊 = '>孢子囊（群）')
    # 孢子叶 = '>孢子叶（球）')
    frequency = RadioInput('>frequency', 'frequency')
    DBH = Number('>DBH')
    height = '>height'
    temporaryIdentification = '>temporaryIdentification'
    dialectName = '>dialectName'
    molecularMaterialSample = '>molecularMaterialSample'
    seedMaterialSample = '>seedMaterialSample'
    livingMaterialSample = '>livingMaterialSample'
    decimalLatitude = GeoCoordinate(('>decimalLatitude', '>decimalLongitude', ';'))
    decimalLongitude = GeoCoordinate(('>decimalLatitude', '>decimalLongitude', ';'))
    minimumElevationInMeters = Number('>minimumElevationInMeters', None, int)
    maximumElevationInMeters = Number('>maximumElevationInMeters', None, int)
    recordedBy = HumanName('>recordedBy')
    recordNumber = '>recordNumber'
    eventDate = DateTime('>eventDate', 'date')
    occurrenceRemarks = '>occurrenceRemarks'


class NsiiTerms(Enum):
    basisOfRecord = RadioInput('>basisOfRecord', 'basisOfRecord')
    rights = '>rights'
    rightsHolder = '>rightsHolder'
    licence = '>licence'
    modified = DateTime('>modified', 'datetime')
    references = '>references'
    institutionCode = RadioInput('>institutionCode', 'institutionCode')
    # Occurrence
    catalogNumber = UniqueID('>catalogNumber')
    recordedBy = HumanName('>recordedBy')
    recordNumber = '>recordNumber'
    individualCount = Number('>individualCount', None, int)
    # Event
    eventDate = DateTime('>eventDate')
    habitat = '>habitat'
    fundedBy = '>fundedBy'
    # Location
    country = AdminDiv(('>country', '>province', '>city', '>county', '::'))
    province = AdminDiv(('>country', '>province', '>city', '>county', '::'))
    city = AdminDiv(('>country', '>province', '>city', '>county', '::'))
    county = AdminDiv(('>country', '>province', '>city', '>county', '::'))
    locality = ('>locality', '>mountain', '>waterBody', ',')
    decimalLatitude = GeoCoordinate(('>decimalLatitude', '>decimalLongitude', ';'))
    decimalLongitude = GeoCoordinate(('>decimalLatitude', '>decimalLongitude', ';'))
    _minimumElevationInMeters = Number('>minimumElevationInMeters')
    _maximumElevationInMeters = Number('>maximumElevationInMeters')
    minimumElevationInMeters = Number('>minimumElevationInMeters', '>maximumElevationInMeters')
    maximumElevationInMeters = Number('>minimumElevationInMeters', '>maximumElevationInMeters')
    _minimumDepthInMeters = Number('>minimumDepthInMeters')
    _maximumDepthInMeters = Number('>maximumDepthInMeters')
    minimumDepthInMeters = Number('>minimumDepthInMeters', '>maximumDepthInMeters')
    maximumDepthInMeters = Number('>minimumDepthInMeters', '>maximumDepthInMeters')
    associatedMedia = '>associatedMedia'
    associatedReferences = '>associatedReferences'
    associatedSequences = '>associatedSequences'
    occurrenceRemarks = '>occurrenceRemarks'
    # Taxon
    kingdom = '>kingdom'
    phylum = '>phylum'
    _class  = '>class'
    order = '>order'
    family = '>family'
    vernacularName = '>vernacularName'
    # Identification
    scientificName = BioName(['>scientificName', ('>genus', '>specificEpithet', '>specificAuthorship', '>taxonRank', '>infraspecificEpithet', '>scientificNameAuthorship', ' ')])
    typeStatus = RadioInput('>typeStatus', 'typeStatus')
    identifiedBy = HumanName('>identifiedBy')
    dateIdentified = DateTime('>dateIdentified')
    identificationRemarks = '>identificationRemarks'
