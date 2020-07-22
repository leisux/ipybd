from enum import Enum
from ipybd import data_cleaner

'''定义的枚举将传递给 core.ReStructureTable 重构原始表格

    经重构的表格，其列名将转换为枚举成员的 name, 枚举成员的值则定义了相应值的进一步处理方式

    枚举的value按序包含三个组成部分:校验功能、位置参数、数据列的数量；
    首个元素为值校验功能，可以是函数或类，如果不需要效验，可为空；
    之后的参数为校值需要传递的一至多个位置参数，若校验功能缺省，则值不做校验；位置参数必须由标
    准列名库中定义的列名作为参数；
    最后的参数用于标注位置参数中实际传递给校验功能的数据列数量，以让程序从参数中区分出哪些参数
    是实际的数据，以便在校验之前做必要的预处理。如下方的 individualCount 字段，虽然校值时，
    需要传递两个位置参数‘individualCount’和'int'，但只有'individualCount' 这个参数是数
    据表中真实有对应的数据列， 而 'int' 参数只是指示程序按照整型数字处理数据而已，因此其最后
    一个值设为 1。

    单个位置参数若需要先由多个标准字段合并而成，则使用()包裹这些字段，被()包裹的字段，最后一个
    值为合并后字段间的连接符，目前只支持使用同样的连接符连接不同字段；若最终希望将多列合并为建
    值对形式，则可设连接符为 ‘dict’，‘list’，‘rowList’, 'jsonObject', 'jsonArray' 等值。

    若某个位置参数可能存在多种形式，所有可能的形式需以[]包裹，如下方 scientificName

    某些参数需要先由多个标准字段先进一步合并组成，而参与合并的字段在实际表中可能有多种处理方式，
    比如植物学名可能是（属名 种加词 种下 命名人）也能是（属名 种加词 种下等级 种下 命名人）学
    名中的 taxonRank 字段有可能就不是一个独立的字段，而是被归并到了 specificEpithet 内，
    类似这种多字段组合而成的位置参数，在定义时，应尽可能使用要素更全的表达式，程序会自动排除表
    达式中无法找到的字段，并利用找到的字段进行组装。

'''

class PlantSpecimenTerms(Enum):
    # organism 对象的属性
    organismRemarks = 'organismRemarks', 1
    # occurrence 对象的属性
    recordedBy = data_cleaner.HumanName, 'recordedBy', 1
    recordNumber = 'recordNumber', 1
    eventTime = data_cleaner.DateTime, 'eventTime', 1
    habitat = 'habitat', 1
    # "behavior" in plant
    habit = data_cleaner.RadioInput, 'habit', 'habit', 1
    associatedMedia = 'associatedMedia', 1
    occurrenceRemarks = 'occurrenceRemarks', 1
    decimalLatitude = data_cleaner.GeoCoordinate, ('decimalLatitude', 'decimalLongitude', ';'), 1
    decimalLongitude = data_cleaner.GeoCoordinate, ('decimalLatitude', 'decimalLongitude', ';'), 1
    minimum_Elevation_In_Meters = data_cleaner.NumericalInterval, 'minimumElevationInMeters', 1
    maximum_Elevation_In_Meters = data_cleaner.NumericalInterval, 'maximumElevationInMeters', 1
    minimumElevationInMeters = data_cleaner.NumericalInterval, 'minimum_Elevation_In_Meters', 'maximum_Elevation_In_Meters', 2
    maximumElevationInMeters = data_cleaner.NumericalInterval, 'minimum_Elevation_In_Meters', 'maximum_Elevation_In_Meters', 2
    country = data_cleaner.AdminDiv, ('country', 'stateProvince', 'city', 'county', '::'), 1
    province = data_cleaner.AdminDiv, ('country', 'stateProvince', 'city', 'county', '::'), 1
    city = data_cleaner.AdminDiv, ('country', 'stateProvince', 'city', 'county', '::'), 1
    county = data_cleaner.AdminDiv, ('country', 'stateProvince', 'city', 'county', '::'), 1
    locality = 'locality', 1
    # specimens 对象的属性
    otherCatalogNumbers = 'otherCatalogNumbers', 1
    preparations = data_cleaner.RadioInput, 'preparations', 'preparations', 1
    individualCount = data_cleaner.NumericalInterval, 'individualCount', None, 'int', 1
    #sex = data_cleaner.RadioInput, 'sex', 'sex', 1
    lifeStage = data_cleaner.RadioInput, 'lifeStage', 'lifeStage', 1
    molecularMaterialSample = data_cleaner.RadioInput, 'molecularMaterialSample', 'molecularMaterialSample', 1
    dynamicProperties = ('flower', 'leaf', 'stem', 'fruit', 'seed', 'root', 'o'), 1
    # identification 对象的属性
    classification = data_cleaner.RadioInput, 'classification', 'classification', 1
    scientificName = data_cleaner.BioName, [('genus', 'specificEpithet', 'specificEpithetAuthorShip', 'taxonRank', 'infraspecificEpithet', 'scientificNameAuthorship', ' '), 'scientificName'], 1
    typeStatus = data_cleaner.RadioInput, 'typeStatus', 'typeStatus', 1
    identifiedBy = data_cleaner.HumanName, 'identifiedBy', 1
    dateIdentified = data_cleaner.DateTime, 'dateIdentified', 1
    identificationRemarks = 'identificationRemarks', 1
    # institution 对象的属性
    institutionCode = data_cleaner.RadioInput, 'institutionCode', 'institutionCode', 1
    catalogNumber = data_cleaner.UniqueID, 'catalogNumber', 1
    disposition = data_cleaner.RadioInput, 'disposition', 'disposition', 1
    preservedTime = data_cleaner.DateTime, 'preservedTime', 1
    preservedLocation = data_cleaner.RadioInput, 'preservedLocation', 'preservedLocation', 1

class Aves(Enum):
    pass

class KingdoniaPlantTerms(Enum):
    catalogNumber = data_cleaner.UniqueID, 'catalogNumber', 1
    institutionCode = data_cleaner.RadioInput, 'institutionCode', 'institutionCode', 1
    otherCatalogNumbers = 'otherCatalogNumbers', 1
    classification = data_cleaner.RadioInput, 'classification', 'classification', 1
    lifeStage = data_cleaner.RadioInput, 'lifeStage', 'lifeStage', 1
    disposition = data_cleaner.RadioInput, 'disposition', 'disposition', 1
    preservedLocation = data_cleaner.RadioInput, 'preservedLocation', 'preservedLocation', 1
    preservedTime = data_cleaner.DateTime, 'preservedTime', 1
    recordedBy = data_cleaner.HumanName, 'recordedBy', 1
    recordNumber = 'recordNumber', 1
    eventTime = data_cleaner.DateTime, 'eventTime', 1
    country = data_cleaner.AdminDiv, ('country', 'stateProvince', 'city', 'county', '::'), 1
    stateProvince = data_cleaner.AdminDiv, ('country', 'stateProvince', 'city', 'county', '::'), 1
    city = data_cleaner.AdminDiv, ('country', 'stateProvince', 'city', 'county', '::'), 1
    county = data_cleaner.AdminDiv, ('country', 'stateProvince', 'city', 'county', '::'), 1
    locality = 'locality', 1
    decimalLatitude = data_cleaner.GeoCoordinate, ('decimalLatitude', 'decimalLongitude', ';'), 1
    decimalLongitude = data_cleaner.GeoCoordinate, ('decimalLatitude', 'decimalLongitude', ';'), 1
    minimum_Elevation_In_Meters = data_cleaner.NumericalInterval, 'minimumElevationInMeters', 1
    maximum_Elevation_In_Meters = data_cleaner.NumericalInterval, 'maximumElevationInMeters', 1
    minimumElevationInMeters = data_cleaner.NumericalInterval, 'minimum_Elevation_In_Meters', 'maximum_Elevation_In_Meters', 2
    maximumElevationInMeters = data_cleaner.NumericalInterval, 'minimum_Elevation_In_Meters', 'maximum_Elevation_In_Meters', 2
    habitat = 'habitat', 1
    habit = data_cleaner.RadioInput, 'habit', 'habit', 1
    dynamicProperties = ('flower', 'leaf', 'stem', 'fruit', 'seed', 'root', 'o'), 1
    organismRemarks = 'organismRemarks', 1
    occurrenceRemarks = 'occurrenceRemarks', 1
    scientific_Name = data_cleaner.BioName, [('genus', 'specificEpithet', 'specificEpithetAuthorShip', 'taxonRank', 'infraspecificEpithet', 'scientificNameAuthorship', ' '), 'scientificName'], 1
    scientificName = data_cleaner.FillNa, 'scientific_Name', 'unknown', 1
    type_Status = data_cleaner.RadioInput, 'typeStatus', 'typeStatus', 1
    typeStatus = data_cleaner.FillNa, 'type_Status', 'not type', 1
    identified_By = data_cleaner.HumanName, 'identifiedBy', 1
    identifiedBy = data_cleaner.FillNa, 'identified_By', '无', 1
    date_Identified = data_cleaner.DateTime, 'dateIdentified', 1
    dateIdentified = data_cleaner.FillNa, 'date_Identified', '0000:00:00 00:00:02', 1
    identifications = ("scientificName", "identifiedBy", "dateIdentified", "typeStatus", "a"), 1
    relationshipEstablishedTime = data_cleaner.DateTime, 'relationshipEstablishedTime', 1
    associatedMedia = 'associatedMedia', 1
    individualCount = data_cleaner.NumericalInterval, 'individualCount', None, 'int', 1
    #MaterialSample