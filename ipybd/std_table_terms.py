from enum import Enum
from ipybd.data_cleaner import *


class CvhTerms(Enum):
    条形码 = UniqueID('$catalogNumber')
    馆代码 = RadioInput('$collectionCode', 'collectionCode')
    流水号 = UniqueID('$otherCatalogNumbers')
    标本状态 = RadioInput('$lifeStage', 'lifeStage')
    库存 = RadioInput('$disposition', 'disposition')
    采集人 = HumanName('$recordedBy')
    采集号 = '$recordNumber'
    份数 = Number('$individualCount', None, int)
    采集日期 = DateTime('$eventDate')
    国家 = '$country'
    province = '$province'
    city = '$city'
    #国家__province__city__区县 = AdminDiv(('$country', '$province', '$city', '$county', '::'))
    省市 = ('$province', '$city', ',')
    区县 = '$county'
    小地点 = ('$locality', '$mountain', '$waterBody', ',')
    纬度__经度 = GeoCoordinate(('$decimalLatitude', '$decimalLongitude', ';'))
    _海拔 = Number('$minimumElevationInMeters')
    _海拔高 = Number('$maximumElevationInMeters')
    海拔__海拔高 = Number('$minimumElevationInMeters', '$maximumElevationInMeters')
    生境 = '$habitat'
    中文名 = '$vernacularName'
    科 = '$family'
    属 = '$genus'
    种加词 = '$specificEpithet'
    种命名人 = '$specificAuthorship'
    种下等级 = '$taxonRank'
    种下加词 = '$infraspecificEpithet'
    种下等级命名人 = '$scientificNameAuthorship'
    拉丁名 = BioName('$scientificName', style='scientificName')
    模式类型 = RadioInput('$typeStatus', 'typeStatus')
    鉴定人 = HumanName('$identifiedBy')
    鉴定日期 = DateTime('$dateIdentified')
    习性 = RadioInput('$habit', 'habit')
    体高 = '$height'
    胸径 = '$DBH'
    频度 = '$frequency'
    花 = '$flower'
    果 = '$fruit'
    叶 = '$leaf'
    茎 = '$stem'
    根 = '$root'
    种子 = '$seed'
    野外鉴定 = '$temporaryIdentification'
    当地名称 = '$dialectName'
    备注 = '$occurrenceRemarks'



class OccurrenceTerms(Enum):
    # Record
    basisOfRecord = RadioInput('$basisOfRecord', 'basisOfRecord')
    rights = '$rights'
    rightsHolder = '$rightsHolder'
    licence = '$licence'
    modified = DateTime('$modified', 'datetime')
    references = '$references'
    collectionCode = RadioInput('$collectionCode', 'collectionCode')
    classification = RadioInput('$classification', 'classification')
    # Occurrence
    OccurrenceID = UniqueID('$occurrenceID')
    catalogNumber = UniqueID('$catalogNumber')
    otherCatalogNumbers = '$otherCatalogNumbers'
    preparations = RadioInput('$preparations', 'preparations')
    disposition = RadioInput('$disposition', 'disposition')
    preservedTime = DateTime('$preservedTime', 'datetime')
    # 柜子位置自行在 std_options_alias 中定义
    preservedLocation = RadioInput('$preservedLocation', 'preservedLocation')
    recordedBy = HumanName('$recordedBy')
    recordNumber = '$recordNumber'
    individualCount = Number('$individualCount', None, int)
    lifeStage = RadioInput('$lifeStage', 'lifeStage')
    sex = RadioInput('$sex', 'sex')
    behavior = '$behavior'
    habit = RadioInput('$habit', 'habit')
    establishmentMeans = RadioInput('$establishmentMeans', 'establishmentMeans')
    molecularMaterialSample = RadioInput('$molecularMaterialSample', 'molecularMaterialSample')
    # Event
    eventDate = DateTime('$eventDate')
    habitat = '$habitat'
    samplingProtocol = RadioInput('$samplingProtocol', 'samplingProtocol')
    fieldNumber = '$fieldNumber'
    fieldNotes = '$fieldNotes'
    fundedBy = '$fundedBy'
    # Location
    country__province__city__county = AdminDiv(('$country', '$province', '$city', '$county', '::'))
    locality = ('$locality', '$mountain', '$waterBody', ',')
    decimalLatitude__decimalLongitude = GeoCoordinate(('$decimalLatitude', '$decimalLongitude', ';'))
    _minimumElevationInMeters = Number('$minimumElevationInMeters')
    _maximumElevationInMeters = Number('$maximumElevationInMeters')
    minimumElevationInMeters__maximumElevationInMeters = Number('$minimumElevationInMeters', '$maximumElevationInMeters')
    _minimumDepthInMeters = Number('$minimumDepthInMeters')
    _maximumDepthInMeters = Number('$maximumDepthInMeters')
    minimumDepthInMeters__maximumDepthInMeters = Number('$minimumDepthInMeters', '$maximumDepthInMeters')
    associatedMedia = '$associatedMedia'
    associatedReferences = '$associatedReferences'
    associatedSequences = '$associatedSequences'
    occurrenceRemarks = '$occurrenceRemarks'
    # Taxon
    kingdom = '$kingdom'
    phylum = '$phylum'
    _class  = '$class'
    order = '$order'
    family = '$family'
    vernacularName = '$vernacularName'
    # Identification
    scientificName = BioName(['$scientificName', ('$genus', '$specificEpithet', '$specificAuthorship', '$taxonRank', '$infraspecificEpithet', '$scientificNameAuthorship', ' ')], style='scientificName')
    typeStatus = RadioInput('$typeStatus', 'typeStatus')
    identifiedBy = HumanName('$identifiedBy')
    dateIdentified = DateTime('$dateIdentified')
    identificationRemarks = '$identificationRemarks'
    # Organism of Plant
    root = '$root'
    stem = '$stem'
    leaf = '$leaf'
    flower = '$flower'
    fruit = '$fruit'
    seed = '$seed'
    # Organism of Aves
    weightInGrams = Number('$weightInGrams')
    bodyLengthInMillimeters = Number('$bodyLengthInMillimeters')
    wingChordInMillimeters = Number('$wingLengthInMillimeters')
    tailLengthInMillimeters = Number('$tailLengthInMillimeters')
    tarsusInMillimeters = Number('$tarsusInMillimeters')
    exposedCulmenInMillimeters = Number('$exposedCulmenInMillimeters')
    irisColor = '$irisColor'
    billColor = '$billColor'
    legsColor = '$legsColor'
    fat = RadioInput('$fat', 'fat')
    heightOfNestInMeters = Number('$heightOfNestInMeters')
    substrateOfNest = '$substrateOfNest'
    constructionOfNest = '$constructionOfNest'
    numOfEggsTaken = Number('$numOfEggsTaken', None, int)
    incubation = '$incubation'
    organismRemarks = '$organismRemarks'


class NoiOccurrenceTerms(Enum):
    # Occurrence Object
    occurrenceID = UniqueID('$occurrenceID')
    catalogNumber = UniqueID('$catalogNumber')
    otherCatalogNumbers = '$otherCatalogNumbers'
    recordedBy = HumanName('$recordedBy')
    recordNumber = '$recordNumber'
    individualCount = Number('$individualCount', None, int)
    sex = RadioInput('$sex', 'sex')
    lifeStage = RadioInput('$lifeStage', 'lifeStage')
    behavior = '$behavior'
    establismentMeans = RadioInput('$establismentMeans', 'establismentMeans')
    preparations = RadioInput('$preparations', 'preparations')
    disposition = RadioInput('$disposition', 'disposition')
    associatedMedia = Url('$associatedMedia')
    associatedReferences = Url('$assocatedReferences')
    associatedSequences = Url('$associatedSequences')
    occurrenceRemarks = '$occurrenceRemarks'
    Occurrence = ('$occurrenceID', '$catalogNumber', '$otherCatalogNumbers', '$recordedBy', '$recordNumber', '$individualCount', '$sex', '$lifeStage', '$behavior', '$establishmentMeans', '$preparations', '$disposition', '$associatedMedia', '$associatedSequences', '$assocatedReferences', '$occurrenceRemarks', 'd')

    # Event Object
    eventDate = DateTime('$eventDate', 'utc')
    habitat = '$habitat'
    fieldNumber = '$fieldNumber'
    samplingProtocol = '$samplingProtocol'
    fieldNotes = '$fieldNotes'
    fundedBy = '$fundedBy'
    Event = ('$eventDate', '$habitat', '$fieldNumber', '$samplingProtocol', '$fieldNotes', '$fundedBy', 'd')

    # Location Object
    countryCode = '$countryCode'
    country = '$country'
    province = '$province'
    city = '$city'
    county = '$county'
    #country__province__city__county = AdminDiv(('$country', '$province', '$city', '$county', '::'))
    locality = ('$locality', '$mountain', '$waterBody', ',')
    decimalLatitude__decimalLongitude = GeoCoordinate(('$decimalLatitude', '$decimalLongitude', ';'))
    _minimumElevationInMeters = Number('$minimumElevationInMeters')
    _maximumElevationInMeters = Number('$maximumElevationInMeters')
    minimumElevationInMeters__maximumElevationInMeters = Number('$minimumElevationInMeters', '$maximumElevationInMeters')
    verbatimElevation = '$verbatimElevation'
    geodeticDatum = RadioInput('$geodeticDatum', 'geodeticDatum')
    georeferenceProtocol = '$georeferenceProtocol'
    _minimumDepthInMeters = Number('$minimumDepthInMeters')
    _maximumDepthInMeters = Number('$maximumDepthInMeters')
    minimumDepthInMeters__maximumDepthInMeters = Number('$minimumDepthInMeters', '$maximumDepthInMeters')
    _minimumDistanceAboveSurfaceInMeters = Number('$minimumDistanceAboveSurfaceInMeters')
    _maximumDistanceAboveSurfaceInMeters = Number('$maximumDistanceAboveSurfaceInMeters')
    minimumDistanceAboveSurfaceInMeters__maximumDistanceAboveSurfaceInMeters = Number('$minimumDistanceAboveSurfaceInMeters', '$maximumDistanceAboveSurfaceInMeters')
    Location = ('$countryCode', '$country', '$province', '$city', '$county', '$locality', '$decimalLatitude', '$decimalLongitude', '$minimumElevationInMeters', '$maximumElevationInMeters', '$verbatimElevation', '$minimumDepthInMeters', '$maximumDepthInMeters', '$geodeticDatum', '$georeferenceProtocol', '$minimumDistanceAboveSurfaceInMeters', '$maximumDistanceAboveSurfaceInMeters', 'd')

    # Idnetification Object
    vernacularName = '$vernacularName'
    scientificName = BioName(['$scientificName', ('$genus', '$specificEpithet', '$specificAuthorship', '$taxonRank', '$infraspecificEpithet', '$scientificNameAuthorship', ' ')])
    identifiedBy = HumanName('$identifiedBy')
    dateIdentified = DateTime('$dateIdentified', 'utc')
    typeStatus = RadioInput('$typeStatus', 'typeStatus')
    _Identification = ('$vernacularName', '$scientificName', '$identifiedBy', '$dateIdentified', '$typeStatus', 'd')
    Identification = ('$Identification', 'l')

    # Record Object
    datasetName = '$datasetName'
    institutionCode = '$institutionCode'
    collectionCode = '$collectionCode'
    category = RadioInput('$category', 'category')
    basisOfRecord = RadioInput('$basisOfRecord', 'basisOfRecord')
    dataFrom = '$dataFrom'
    rightsHolder = '$rightsHolder'
    references = '$references'
    dataApi = '$dataApi'
    thumbnails = '$thumbnails'
    license = '$licence'
    modified = DateTime('$modified', 'utc')
    Record = ('$datasetName', '$institutionCode', '$collectionCode', '$category', '$basisOfRecord', '$dataFrom', '$rightsHolder', '$references', '$dataApi', '$thumbnails', '$license', '$modified', 'd')
    DictForNoiOccurrence = ('$Occurrence', '$Location', '$Identification', '$Event', '$Record', 'd')


class KingdoniaPlantTerms(Enum):
    catalogNumber = UniqueID('$catalogNumber')
    institutionCode = RadioInput('$collectionCode', 'collectionCode')
    otherCatalogNumbers = '$otherCatalogNumbers'
    classification = RadioInput('$classification', 'classification')
    lifeStage = RadioInput('$lifeStage', 'lifeStage')
    disposition = RadioInput('$disposition', 'disposition')
    preservedLocation = RadioInput('$preservedLocation', 'preservedLocation')
    preservedTime = DateTime('$preservedTime', 'utc')
    recordedBy = HumanName('$recordedBy')
    recordNumber = '$recordNumber'
    eventDate = DateTime('$eventDate', 'datetime')
    _individualCount = Number('$individualCount', None, int)
    individualCount = FillNa('$individualCount', 0)
    country__stateProvince__city__county = AdminDiv(('$country', '$province', '$city', '$county', '::'))
    locality = ('$locality', '$mountain', '$waterBody', ',')
    habitat = '$habitat'
    habit = RadioInput('$habit', 'habit')
    decimalLatitude__decimalLongitude = GeoCoordinate(('$decimalLatitude', '$decimalLongitude', ';'))
    _minimumElevationInMeters = Number('$minimumElevationInMeters')
    _maximumElevationInMeters = Number('$maximumElevationInMeters')
    minimumElevationInMeters__maximumElevationInMeters = Number('$minimumElevationInMeters', '$maximumElevationInMeters')
    occurrenceRemarks = '$occurrenceRemarks'
    _scientificName = BioName(['$scientificName', ('$genus', '$specificEpithet', '$taxonRank', '$infraspecificEpithet', ' ')], style='simpleName')
    scientificName = FillNa('$scientificName', 'unknown')
    _typeStatus = RadioInput('$typeStatus', 'typeStatus')
    typeStatus = FillNa('$typeStatus', 'not type')
    _identifiedBy = HumanName('$identifiedBy')
    identifiedBy = FillNa('$identifiedBy', '无')
    _dateIdentified = DateTime('$dateIdentified', 'datetime')
    dateIdentified = FillNa('$dateIdentified', '0000:00:00 00:00:02')
    _identifiedByID = UniqueID('$identifiedByID')
    identifiedByID = FillNa('$identifiedByID', '0')
    _identifications = ('$scientificName', '$identifiedByID', '$identifiedBy',  '$dateIdentified', '$typeStatus', 'l')
    identifications = ('$identifications', 'l')
    花 = '$flower'
    叶 = '$leaf'
    茎 = '$stem'
    果实 = '$fruit'
    种子 = '$seed'
    根 = '$root'
    不定根 = '$rhizoids'
    #孢子囊（群）= '$孢子囊（群）')
    #孢子叶（球）= '$孢子叶（球）')
    频度 = RadioInput('$frequency', 'frequency')
    胸径 = Number('$DBH')
    体高 = '$height'
    野外鉴定 = '$temporaryIdentification'
    当地名称 = '$dialectName'
    dynamicProperties = ('$频度', '$胸径', '$体高', '$孢子囊（群）', '$孢子叶（球）', '$花', '$叶', '$茎', '$果实', '$种子', '$根', '$不定根', '$野外鉴定', '$当地名称', 'o')
    organismRemarks = '$organismRemarks'
    associatedMedia = '$associatedMedia'
    _molecularMaterialSample = RadioInput('$molecularMaterialSample', 'molecularMaterialSample')
    molecularMaterialSample = FillNa('$molecularMaterialSample', '无')
    _seedMaterialSample = Number('$seedMaterialSample', None, int)
    seedMaterialSample = FillNa('$seedMaterialSample', 0)
    _livingMaterialSample = Number('$livingMaterialSample', None, int)
    livingMaterialSample = FillNa('$livingMaterialSample', 0)
    MaterialSample = ('$molecularMaterialSample', '$seedMaterialSample', '$livingMaterialSample', 'o')


class KingdoniaAvesTerms(Enum):
    pass


class HerbLabelTerms(Enum):
    duplicatesOfLabel = Number('$duplicatesOfLabel', None, int)
    labelTitle = ['$labelTitle', '$institutionCode']
    labelNote = ['$labelNote', '$collectionCode']
    labelSubtitle = ['$labelSubtitle', '$fundedBy']
    family = '$family'
    vernacularName = '$vernacularName'
    genus__specificEpithet__taxonRank__infraspecificEpithet__scientificNameAuthorship = BioName(['$scientificName', ('$genus', '$specificEpithet',  'specificAuthorship', '$taxonRank', '$infraspecificEpithet', '$scientificNameAuthorship', ' ')], style='plantSplitName')
    identifiedBy = HumanName('$identifiedBy')
    dateIdentified = DateTime('$dateIdentified', 'date')
    country__province__city__county = AdminDiv(('$country', '$province', '$city', '$county', '::'))
    locality = ('$locality', '$mountain', '$waterBody', ',')
    habitat = '$habitat'
    individualCount = Number('$individualCount', None, int)
    habit = RadioInput('$habit', 'habit')
    flower = '$flower'
    leaf = '$leaf'
    stem = '$stem'
    fruit = '$fruit'
    seed = '$seed'
    root = '$root'
    rhizoids = '$rhizoids'
    # 孢子囊 = '$孢子囊（群）')
    # 孢子叶 = '$孢子叶（球）')
    frequency = RadioInput('$frequency', 'frequency')
    DBH = Number('$DBH')
    height = '$height'
    temporaryIdentification = '$temporaryIdentification'
    dialectName = '$dialectName'
    molecularMaterialSample = '$molecularMaterialSample'
    seedMaterialSample = '$seedMaterialSample'
    livingMaterialSample = '$livingMaterialSample'
    decimalLatitude__decimalLongitude = GeoCoordinate(('$decimalLatitude', '$decimalLongitude', ';'))
    minimumElevationInMeters = Number('$minimumElevationInMeters', None, int)
    maximumElevationInMeters = Number('$maximumElevationInMeters', None, int)
    recordedBy = HumanName('$recordedBy')
    recordNumber = '$recordNumber'
    eventDate = DateTime('$eventDate', 'date')
    occurrenceRemarks = '$occurrenceRemarks'


class NsiiTerms(Enum):
    basisOfRecord = RadioInput('$basisOfRecord', 'basisOfRecord')
    rights = '$rights'
    rightsHolder = '$rightsHolder'
    licence = '$licence'
    modified = DateTime('$modified', 'datetime')
    references = '$references'
    collectionCode = RadioInput('$collectionCode', 'collectionCode')
    # Occurrence
    catalogNumber = UniqueID('$catalogNumber')
    recordedBy = HumanName('$recordedBy')
    recordNumber = '$recordNumber'
    individualCount = Number('$individualCount', None, int)
    # Event
    eventDate = DateTime('$eventDate')
    habitat = '$habitat'
    fundedBy = '$fundedBy'
    # Location
    country__province__city__county = AdminDiv(('$country', '$province', '$city', '$county', '::'))
    locality = ('$locality', '$mountain', '$waterBody', ',')
    decimalLatitude__decimalLongitude = GeoCoordinate(('$decimalLatitude', '$decimalLongitude', ';'))
    _minimumElevationInMeters = Number('$minimumElevationInMeters')
    _maximumElevationInMeters = Number('$maximumElevationInMeters')
    minimumElevationInMeters__maximumElevationInMeters = Number('$minimumElevationInMeters', '$maximumElevationInMeters')
    _minimumDepthInMeters = Number('$minimumDepthInMeters')
    _maximumDepthInMeters = Number('$maximumDepthInMeters')
    minimumDepthInMeters__maximumDepthInMeters = Number('$minimumDepthInMeters', '$maximumDepthInMeters')
    associatedMedia = '$associatedMedia'
    associatedReferences = '$associatedReferences'
    associatedSequences = '$associatedSequences'
    occurrenceRemarks = '$occurrenceRemarks'
    # Taxon
    kingdom = '$kingdom'
    phylum = '$phylum'
    _class  = '$class'
    order = '$order'
    family = '$family'
    vernacularName = '$vernacularName'
    # Identification
    scientificName = BioName(['$scientificName', ('$genus', '$specificEpithet', '$specificAuthorship', '$taxonRank', '$infraspecificEpithet', '$scientificNameAuthorship', ' ')])
    typeStatus = RadioInput('$typeStatus', 'typeStatus')
    identifiedBy = HumanName('$identifiedBy')
    dateIdentified = DateTime('$dateIdentified')

    identificationRemarks = '$identificationRemarks'
