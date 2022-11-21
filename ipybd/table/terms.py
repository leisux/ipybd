from enum import Enum

from ipybd.function.cleaner import *


class CvhTerms(Enum):
    条形码_ = UniqueID('$catalogNumber')
    馆代码_ = RadioInput('$collectionCode', 'collectionCode')
    流水号_ = UniqueID('$otherCatalogNumbers')
    模式类型_ = RadioInput('$typeStatus', 'typeStatus')
    库存_ = RadioInput('$disposition', 'disposition')
    标本状态_ = RadioInput('$reproductiveCondition', 'reproductiveCondition')
    采集人_ = HumanName('$recordedBy')
    采集号_ = '$recordNumber'
    采集日期_ = DateTime('$eventDate')
    份数_ = Number('$individualCount', None, int)
    国家_ = '$country'
    province = '$province'
    prefecture = '$prefecture'
    #国家__province__prefecture__区县 = AdminDiv(('$country', '$province', '$prefecture', '$county', '::'))
    省市_ = ('$province', '$prefecture', ',')
    区县_ = '$county'
    小地点_ = ('$locality', '$mountain', '$waterBody', ',')
    生境_ = '$habitat'
    科_ = '$family'
    属__种__定名人__种下等级__种下加词__种下等级定名人_ = BioName(['$scientificName', ('$genus', '$specificEpithet', '$specificAuthorship', '$taxonRank', '$infraspecificEpithet', '$scientificNameAuthorship', ' ')], style='fullPlantSplitName')
    种下等级 = ('$种下等级', '$种下加词', ' ')
    拉丁名__ = ('$属', '$种', '$定名人', '$种下等级', '$种下等级定名人', ' ')
    中文名_ = '$chineseName'
    鉴定人_ = HumanName('$identifiedBy')
    鉴定日期_ = DateTime('$dateIdentified')
    纬度__经度_ = GeoCoordinate(['$verbatimCoordinates', ('$decimalLatitude', '$decimalLongitude', ';')])
    minimumElevationInMeters__maximumElevationInMeters = {'$verbatimElevation': '-'}
    minimumElevationInMeters_ = Number('$minimumElevationInMeters')
    maximumElevationInMeters_ = Number('$maximumElevationInMeters')
    海拔__海拔高 = Number('$minimumElevationInMeters', '$maximumElevationInMeters')
    备注_ = '$occurrenceRemarks'
    习性_ = RadioInput('$lifeForm', 'lifeForm')
    体高_ = '$height'
    胸径_ = '$DBH'
    树皮_ = '$stem'
    叶_ = '$leaf'
    花_ = '$reproductiveOrgans'
    果实_ = ('$fruit', '$propagulum')
    寄主_ = '$host'
    备注2_ = '$organismRemarks'


class OccurrenceTerms(Enum):
    # Record
    basisOfRecord = RadioInput('$basisOfRecord', 'basisOfRecord')
    rights = '$rights'
    rightsHolder = '$rightsHolder'
    license = '$license'
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
    reproductiveCondition = RadioInput('$reproductiveCondition', 'reproductiveCondition')
    lifeStage = RadioInput('$lifeStage', 'lifeStage')
    sex = RadioInput('$sex', 'sex')
    behavior = '$behavior'
    lifeForm = RadioInput('$lifeForm', 'lifeForm')
    establishmentMeans = RadioInput('$establishmentMeans', 'establishmentMeans')
    molecularMaterialSample = RadioInput('$molecularMaterialSample', 'molecularMaterialSample')
    # Event
    eventDate = DateTime('$eventDate')
    habitat = '$habitat'
    substrate = '$substrate'
    samplingProtocol = RadioInput('$samplingProtocol', 'samplingProtocol')
    fieldNumber = '$fieldNumber'
    fieldNotes = '$fieldNotes'
    fundedBy = '$fundedBy'
    # Location
    country__province__prefecture__county = AdminDiv([('$country', '$province', '$prefecture', '$county', '::'), '$higherGeography'])
    locality = ('$locality', '$mountain', '$waterBody', ',')
    decimalLatitude__decimalLongitude = GeoCoordinate(['$verbatimCoordinates', ('$decimalLatitude', '$decimalLongitude', ';')])
    _minimumElevationInMeters__maximumElevationInMeters = {'$verbatimElevation': '-'}
    minimumElevationInMeters = Number('$minimumElevationInMeters')
    maximumElevationInMeters = Number('$maximumElevationInMeters')
    minimumElevationInMeters__maximumElevationInMeters = Number('$minimumElevationInMeters', '$maximumElevationInMeters')
    _minimumDepthInMeters__maximumDepthInMeters = {'$verbatimDepth': '-'}
    minimumDepthInMeters = Number('$minimumDepthInMeters')
    maximumDepthInMeters = Number('$maximumDepthInMeters')
    minimumDepthInMeters__maximumDepthInMeters = Number('$minimumDepthInMeters', '$maximumDepthInMeters')
    associatedMedia = '$associatedMedia'
    associatedReferences = '$associatedReferences'
    associatedSequences = '$associatedSequences'
    occurrenceRemarks = '$occurrenceRemarks'
    # Taxon
    kingdomChineseName = '$kingdomChineseName'
    kingdom = '$kingdom'
    phylumChineseName = '$phylumChineseName'
    phylum = '$phylum'
    classChineseName = '$classChineseName'
    _class  = '$class'
    orderChineseName = '$orderChineseName'
    order = '$order'
    familyChineseName = '$familyChineseName'
    family = '$family'
    # Identification
    chineseName = '$chineseName'
    scientificName = BioName(['$scientificName', ('$genus', '$specificEpithet', '$specificAuthorship', '$taxonRank', '$infraspecificEpithet', '$scientificNameAuthorship', ' ')], style='scientificName')
    typeStatus = RadioInput('$typeStatus', 'typeStatus')
    identifiedBy = HumanName('$identifiedBy')
    dateIdentified = DateTime('$dateIdentified')
    identificationRemarks = '$identificationRemarks'
    # Organism of Plant
    reproductiveOrgans = '$reproductiveOrgans'
    leaf = '$leaf'
    stem = '$stem'
    fruit = '$fruit'
    propagulum = '$propagulum'
    root = '$root'
    adventitiousRoot_ = '$adventitiousRoot' 
    rhizoids_ = '$rhizoids'
    host = "$host"
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
    # 需要增加 reproductiveCondition
    # NOI 后续更新后，需要将字段名改为 reproductiveCondition
    lifeStage = RadioInput('$reproductiveCondition', 'reproductiveCondition')
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
    # 等模型改过来后， city 后续需要改为 prefecture
    city = '$prefecture'
    county = '$county'
    #country__province__prefecture__county = AdminDiv(('$country', '$province', '$prefecture', '$county', '::'))
    locality = ('$locality', '$mountain', '$waterBody', ',')
    decimalLatitude__decimalLongitude = GeoCoordinate(['$verbatimCoordinates', ('$decimalLatitude', '$decimalLongitude', ';')])
    # _minimumElevationInMeters__maximumElevationInMeters = {'$verbatimElevation': '-'}
    minimumElevationInMeters = Number('$minimumElevationInMeters')
    maximumElevationInMeters = Number('$maximumElevationInMeters')
    minimumElevationInMeters__maximumElevationInMeters = Number('$minimumElevationInMeters', '$maximumElevationInMeters')
    verbatimElevation = '$verbatimElevation'
    geodeticDatum = RadioInput('$geodeticDatum', 'geodeticDatum')
    georeferenceProtocol = '$georeferenceProtocol'
    _minimumDepthInMeters__maximumDepthInMeters = {'$verbatimDepth': '-'}
    minimumDepthInMeters = Number('$minimumDepthInMeters')
    maximumDepthInMeters = Number('$maximumDepthInMeters')
    minimumDepthInMeters__maximumDepthInMeters = Number('$minimumDepthInMeters', '$maximumDepthInMeters')
    minimumDistanceAboveSurfaceInMeters = Number('$minimumDistanceAboveSurfaceInMeters')
    maximumDistanceAboveSurfaceInMeters = Number('$maximumDistanceAboveSurfaceInMeters')
    minimumDistanceAboveSurfaceInMeters__maximumDistanceAboveSurfaceInMeters = Number('$minimumDistanceAboveSurfaceInMeters', '$maximumDistanceAboveSurfaceInMeters')
    Location = ('$countryCode', '$country', '$province', '$city', '$county', '$locality', '$decimalLatitude', '$decimalLongitude', '$minimumElevationInMeters', '$maximumElevationInMeters', '$verbatimElevation', '$minimumDepthInMeters', '$maximumDepthInMeters', '$geodeticDatum', '$georeferenceProtocol', '$minimumDistanceAboveSurfaceInMeters', '$maximumDistanceAboveSurfaceInMeters', 'd')

    # Idnetification Object
    # vernacularName 现已更名为 chineseName
    vernacularName = '$chineseName'
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
    license = '$license'
    modified = DateTime('$modified', 'utc')
    Record = ('$datasetName', '$institutionCode', '$collectionCode', '$category', '$basisOfRecord', '$dataFrom', '$rightsHolder', '$references', '$dataApi', '$thumbnails', '$license', '$modified', 'd')
    DictForNoiOccurrence = ('$Occurrence', '$Location', '$Identification', '$Event', '$Record', 'd')


class KingdoniaPlantTerms(Enum):
    catalogNumber_ = UniqueID('$catalogNumber')
    institutionCode_ = RadioInput('$collectionCode', 'collectionCode')
    otherCatalogNumbers_ = '$otherCatalogNumbers'
    classification_ = RadioInput('$classification', 'classification')
    # Kingdonia 后续更新后，需要将字段名改为 reproductiveCondition
    lifeStage_ = RadioInput('$reproductiveCondition', 'reproductiveCondition')
    disposition_ = RadioInput('$disposition', 'disposition')
    preservedLocation_ = RadioInput('$preservedLocation', 'preservedLocation')
    preservedTime_ = DateTime('$preservedTime', 'utc')
    recordedBy_ = HumanName('$recordedBy', separator=',')
    recordNumber_ = '$recordNumber'
    eventDate_ = DateTime('$eventDate', 'datetime')
    individualCount_ = Number('$individualCount', None, int)
    individualCount = FillNa('$individualCount', 0)
    # 等模型改过来后， city 后续需要改为 prefecture
    country__stateProvince__city__county_ = AdminDiv([('$country', '$province', '$prefecture', '$county', '::'), '$higherGeography'])
    locality_ = ('$locality', '$mountain', '$waterBody', ',')
    habitat_ = '$habitat'
    habitat = FillNa('$habitat', '无')
    habit_ = RadioInput('$lifeForm', 'lifeForm')
    decimalLatitude__decimalLongitude_ = GeoCoordinate(['$verbatimCoordinates', ('$decimalLatitude', '$decimalLongitude', ';')])
    decimalLatitude = FillNa('$decimalLatitude', 0)
    decimalLongitude = FillNa('$decimalLongitude', 0)
    _minimumElevationInMeters__maximumElevationInMeters = {'$verbatimElevation': '-'}
    minimumElevationInMeters_ = Number('$minimumElevationInMeters')
    maximumElevationInMeters_ = Number('$maximumElevationInMeters')
    minimumElevationInMeters__maximumElevationInMeters = Number('$minimumElevationInMeters', '$maximumElevationInMeters')
    occurrenceRemarks_ = '$occurrenceRemarks'
    scientificName_ = BioName(['$scientificName', ('$genus', '$specificEpithet', '$taxonRank', '$infraspecificEpithet', ' ')], style='simpleName')
    scientificName = FillNa('$scientificName', 'unknown')
    typeStatus_ = RadioInput('$typeStatus', 'typeStatus')
    typeStatus = FillNa('$typeStatus', 'not type')
    identifiedBy_ = HumanName('$identifiedBy')
    identifiedBy = FillNa('$identifiedBy', '无')
    dateIdentified_ = DateTime('$dateIdentified', 'datetime')
    dateIdentified = FillNa('$dateIdentified', '0000:00:00 00:00:02')
    identifiedByID_ = UniqueID('$identifiedByID')
    identifiedByID = FillNa('$identifiedByID', '0')
    _identifications = ('$scientificName', '$identifiedByID', '$identifiedBy',  '$dateIdentified', '$typeStatus', 'l')
    identifications = ('$identifications', 'l')
    花 = "reproductiveOrgans"
    叶 = '$leaf'
    茎 = '$stem'
    果实 = '$fruit'
    种子 = '$propagulum'
    根 = '$root'
    不定根 = '$adventitiousRoot'
    #孢子囊（群）= '$孢子囊（群）')
    #孢子叶（球）= '$孢子叶（球）')
    # 后续需将其改为 abundance
    频度 = RadioInput('$frequence', 'frequence')
    胸径 = Number('$DBH')
    体高 = '$height'
    野外鉴定 = '$verbatimIdentification'
    当地名称 = '$dialectName'
    dynamicProperties_ = ('$频度', '$胸径', '$体高', '$孢子囊（群）', '$孢子叶（球）', '$花', '$叶', '$茎', '$果实', '$种子', '$根', '$不定根', '$野外鉴定', '$当地名称', 'o')
    organismRemarks_ = '$organismRemarks'
    associatedMedia_ = '$associatedMedia'
    molecularMaterialSample_ = RadioInput('$molecularMaterialSample', 'molecularMaterialSample')
    molecularMaterialSample = FillNa('$molecularMaterialSample', '无')
    seedMaterialSample_ = Number('$seedMaterialSample', None, int)
    seedMaterialSample = FillNa('$seedMaterialSample', 0)
    livingMaterialSample_ = Number('$livingMaterialSample', None, int)
    livingMaterialSample = FillNa('$livingMaterialSample', 0)
    MaterialSample = ('$molecularMaterialSample', '$seedMaterialSample', '$livingMaterialSample', 'o')


class KingdoniaAvesTerms(Enum):
    pass


class HerbLabelTerms(Enum):
    catalogNumber_ = UniqueID('$catalogNumber')
    otherCatalogNumbers_ = '$otherCatalogNumbers'
    duplicatesOfLabel_ = Number('$duplicatesOfLabel', None, int)
    labelTitle_ = ['$labelTitle', '$institutionCode']
    labelNote_ = ['$labelNote', '$collectionCode']
    labelSubtitle_ = ['$labelSubtitle', '$fundedBy']
    creator_ = '$creator'
    dateCreated_ = '$dateCreated'
    recordedBy_ = HumanName('$recordedBy')
    recordNumber_ = '$recordNumber'
    eventDate_ = DateTime('$eventDate', 'date')
    decimalLatitude__decimalLongitude_ = GeoCoordinate(['$verbatimCoordinates', ('$decimalLatitude', '$decimalLongitude', ';')])
    _minimumElevationInMeters__maximumElevationInMeters = {'$verbatimElevation': '-'}
    minimumElevationInMeters_ = Number('$minimumElevationInMeters', typ=int)
    maximumElevationInMeters = Number('$maximumElevationInMeters', typ=int)
    # minimumElevationInMeters__maximumElevationInMeters = Number('$minimumElevationInMeters', '$maximumElevationInMeters')
    country__province__prefecture__county_ = AdminDiv([('$country', '$province', '$prefecture', '$county', '::'), '$higherGeography'])
    locality_ = ('$locality', '$mountain', '$waterBody', ',')
    verbatimLocality = '$verbatimLocality'
    habitat_ = '$habitat'
    substrate_ = '$substrate'
    individualCount_ = Number('$individualCount', None, int)
    lifeForm_ = RadioInput('$lifeForm', 'lifeForm')
    familyChineseName_ = '$familyChineseName'
    family_ = '$family'
    chineseName= '$chineseName'
    genus__specificEpithet__taxonRank__infraspecificEpithet__scientificNameAuthorship_ = BioName(['$scientificName', ('$genus', '$specificEpithet',  '$specificAuthorship', '$taxonRank', '$infraspecificEpithet', '$scientificNameAuthorship', ' ')], style='plantSplitName')
    identifiedBy_ = HumanName('$identifiedBy')
    dateIdentified_ = DateTime('$dateIdentified', 'date')
    reproductiveOrgans_ = '$reproductiveOrgans'
    leaf_ = '$leaf'
    stem_ = '$stem'
    fruit_ = '$fruit'
    propagulum_ = '$propagulum'
    root_ = '$root'
    adventitiousRoot_ = '$adventitiousRoot' 
    rhizoids_ = '$rhizoids'
    host_ = '$host'
    abundance_ = RadioInput('$abundance', 'abundance')
    DBH_ = Number('$DBH')
    height_ = '$height'
    verbatimIdentification_ = '$verbatimIdentification'
    vernacularName_ = '$vernacularName'
    molecularMaterialSample_ = '$molecularMaterialSample'
    seedMaterialSample_ = '$seedMaterialSample'
    livingMaterialSample_ = '$livingMaterialSample'
    occurrenceRemarks_ = '$occurrenceRemarks'


class NsiiTerms(Enum):
    basisOfRecord_ = RadioInput('$basisOfRecord', 'basisOfRecord')
    rightsHolder_ = '$rightsHolder'
    license_ = '$license'
    modified_ = DateTime('$modified', 'datetime')
    references_ = '$references'
    collectionCode_ = RadioInput('$collectionCode', 'collectionCode')
    # Occurrence
    catalogNumber_ = UniqueID('$catalogNumber')
    recordedBy_ = HumanName('$recordedBy')
    recordNumber_ = '$recordNumber'
    individualCount_ = Number('$individualCount', None, int)
    # Event
    eventDate_ = DateTime('$eventDate')
    habitat_ = '$habitat'
    fundedBy_ = '$fundedBy'
    # Location
    country__province__prefecture__county_ = AdminDiv([('$country', '$province', '$prefecture', '$county', '::'), '$higherGeography'])
    locality_ = ('$locality', '$mountain', '$waterBody', ',')
    decimalLatitude__decimalLongitude_ = GeoCoordinate(['$verbatimCoordinates', ('$decimalLatitude', '$decimalLongitude', ';')])
    _minimumElevationInMeters__maximumElevationInMeters = {'$verbatimElevation': '-'}
    minimumElevationInMeters_ = Number('$minimumElevationInMeters')
    maximumElevationInMeters = Number('$maximumElevationInMeters')
    minimumElevationInMeters__maximumElevationInMeters = Number('$minimumElevationInMeters', '$maximumElevationInMeters')
    _minimumDepthInMeters__maximumDepthInMeters = {'$verbatimDepth': '-'}
    minimumDepthInMeters = Number('$minimumDepthInMeters')
    maximumDepthInMeters = Number('$maximumDepthInMeters')
    minimumDepthInMeters__maximumDepthInMeters = Number('$minimumDepthInMeters', '$maximumDepthInMeters')
    associatedMedia = '$associatedMedia'
    associatedReferences = '$associatedReferences'
    associatedSequences = '$associatedSequences'
    occurrenceRemarks = '$occurrenceRemarks'
    # Taxon
    kingdom_ = '$kingdom'
    phylum_ = '$phylum'
    class_  = '$class'
    order_ = '$order'
    family_ = '$family'
    chineseName_ = '$chineseName'
    # Identification
    scientificName_ = BioName(['$scientificName', ('$genus', '$specificEpithet', '$specificAuthorship', '$taxonRank', '$infraspecificEpithet', '$scientificNameAuthorship', ' ')])
    typeStatus_ = RadioInput('$typeStatus', 'typeStatus')
    identifiedBy_ = HumanName('$identifiedBy')
    dateIdentified_ = DateTime('$dateIdentified')
    identificationRemarks_ = '$identificationRemarks'
