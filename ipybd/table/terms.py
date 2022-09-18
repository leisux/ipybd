from enum import Enum

from ipybd.function.cleaner import *


class CvhTerms(Enum):
    条形码_ = UniqueID('$catalogNumber')
    馆代码_ = RadioInput('$collectionCode', 'collectionCode')
    流水号_ = UniqueID('$otherCatalogNumbers')
    模式类型_ = RadioInput('$typeStatus', 'typeStatus')
    库存_ = RadioInput('$disposition', 'disposition')
    标本状态_ = RadioInput('$lifeStage', 'lifeStage')
    采集人_ = HumanName('$recordedBy')
    采集号_ = '$recordNumber'
    采集日期_ = DateTime('$eventDate')
    份数_ = Number('$individualCount', None, int)
    国家_ = '$country'
    province = '$province'
    city = '$city'
    #国家__province__city__区县 = AdminDiv(('$country', '$province', '$city', '$county', '::'))
    省市_ = ('$province', '$city', ',')
    区县_ = '$county'
    小地点_ = ('$locality', '$mountain', '$waterBody', ',')
    生境_ = '$habitat'
    科_ = '$family'
    属__种__定名人__种下等级__种下加词__种下等级定名人_ = BioName(['$scientificName', ('$genus', '$specificEpithet', '$specificAuthorship', '$taxonRank', '$infraspecificEpithet', '$scientificNameAuthorship', ' ')], style='fullPlantSplitName')
    种下等级 = ('$种下等级', '$种下加词', ' ')
    拉丁名__ = ('$属', '$种', '$定名人', '$种下等级', '$种下等级定名人', ' ')
    中文名_ = '$vernacularName'
    鉴定人_ = HumanName('$identifiedBy')
    鉴定日期_ = DateTime('$dateIdentified')
    纬度__经度_ = GeoCoordinate(['$verbatimCoordinates', ('$decimalLatitude', '$decimalLongitude', ';')])
    minimumElevationInMeters__maximumElevationInMeters = {'$verbatimElevation': '-'}
    minimumElevationInMeters_ = Number('$minimumElevationInMeters')
    maximumElevationInMeters_ = Number('$maximumElevationInMeters')
    海拔__海拔高 = Number('$minimumElevationInMeters', '$maximumElevationInMeters')
    备注_ = '$occurrenceRemarks'
    习性_ = RadioInput('$habit', 'habit')
    体高_ = '$height'
    胸径_ = '$DBH'
    树皮_ = '$stem'
    叶_ = '$leaf'
    花_ = '$flower'
    果实_ = '$fruit'
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
    country__province__city__county = AdminDiv([('$country', '$province', '$city', '$county', '::'), '$higherGeography'])
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
    license = '$license'
    modified = DateTime('$modified', 'utc')
    Record = ('$datasetName', '$institutionCode', '$collectionCode', '$category', '$basisOfRecord', '$dataFrom', '$rightsHolder', '$references', '$dataApi', '$thumbnails', '$license', '$modified', 'd')
    DictForNoiOccurrence = ('$Occurrence', '$Location', '$Identification', '$Event', '$Record', 'd')


class KingdoniaPlantTerms(Enum):
    catalogNumber_ = UniqueID('$catalogNumber')
    institutionCode_ = RadioInput('$collectionCode', 'collectionCode')
    otherCatalogNumbers_ = '$otherCatalogNumbers'
    classification_ = RadioInput('$classification', 'classification')
    lifeStage_ = RadioInput('$lifeStage', 'lifeStage')
    disposition_ = RadioInput('$disposition', 'disposition')
    preservedLocation_ = RadioInput('$preservedLocation', 'preservedLocation')
    preservedTime_ = DateTime('$preservedTime', 'utc')
    recordedBy_ = HumanName('$recordedBy', separator=',')
    recordNumber_ = '$recordNumber'
    eventDate_ = DateTime('$eventDate', 'datetime')
    individualCount_ = Number('$individualCount', None, int)
    individualCount = FillNa('$individualCount', 0)
    country__stateProvince__city__county_ = AdminDiv([('$country', '$province', '$city', '$county', '::'), '$higherGeography'])
    locality_ = ('$locality', '$mountain', '$waterBody', ',')
    habitat_ = '$habitat'
    habitat = FillNa('$habitat', '无')
    habit_ = RadioInput('$habit', 'habit')
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
    recordedBy_ = HumanName('$recordedBy')
    recordNumber_ = '$recordNumber'
    eventDate_ = DateTime('$eventDate', 'date')
    decimalLatitude__decimalLongitude_ = GeoCoordinate(['$verbatimCoordinates', ('$decimalLatitude', '$decimalLongitude', ';')])
    _minimumElevationInMeters__maximumElevationInMeters = {'$verbatimElevation': '-'}
    minimumElevationInMeters_ = Number('$minimumElevationInMeters')
    maximumElevationInMeters = Number('$maximumElevationInMeters')
    minimumElevationInMeters__maximumElevationInMeters = Number('$minimumElevationInMeters', '$maximumElevationInMeters')
    country__province__city__county_ = AdminDiv([('$country', '$province', '$city', '$county', '::'), '$higherGeography'])
    locality_ = ('$locality', '$mountain', '$waterBody', ',')
    habitat_ = '$habitat'
    individualCount_ = Number('$individualCount', None, int)
    habit_ = RadioInput('$habit', 'habit')
    family_ = '$family'
    vernacularName_ = '$vernacularName'
    genus__specificEpithet__taxonRank__infraspecificEpithet__scientificNameAuthorship_ = BioName(['$scientificName', ('$genus', '$specificEpithet',  '$specificAuthorship', '$taxonRank', '$infraspecificEpithet', '$scientificNameAuthorship', ' ')], style='plantSplitName')
    identifiedBy_ = HumanName('$identifiedBy')
    dateIdentified_ = DateTime('$dateIdentified', 'date')
    flower_ = '$flower'
    leaf_ = '$leaf'
    stem_ = '$stem'
    fruit_ = '$fruit'
    seed_ = '$seed'
    root_ = '$root'
    rhizoids_ = '$rhizoids'
    # 孢子囊 = '$孢子囊（群）')
    # 孢子叶 = '$孢子叶（球）')
    frequency_ = RadioInput('$frequency', 'frequency')
    DBH_ = Number('$DBH')
    height_ = '$height'
    temporaryIdentification_ = '$temporaryIdentification'
    dialectName_ = '$dialectName'
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
    country__province__city__county_ = AdminDiv([('$country', '$province', '$city', '$county', '::'), '$higherGeography'])
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
    vernacularName_ = '$vernacularName'
    # Identification
    scientificName_ = BioName(['$scientificName', ('$genus', '$specificEpithet', '$specificAuthorship', '$taxonRank', '$infraspecificEpithet', '$scientificNameAuthorship', ' ')])
    typeStatus_ = RadioInput('$typeStatus', 'typeStatus')
    identifiedBy_ = HumanName('$identifiedBy')
    dateIdentified_ = DateTime('$dateIdentified')
    identificationRemarks_ = '$identificationRemarks'
