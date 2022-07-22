from enum import Enum

class Name(Enum):
    added = "added"
    author = "name author"
    basionym = "basionym"
    basionym_author = "basionym author"
    bibliographic_reference = "bibliographic reference"
    citation_type = "citation type"
    collection_number = "collection number"
    collectors = "collector team"
    distribution = "distribution"
    family = "family"
    full_name = "full name"
    genus = "genus"
    in_powo = "in powo"
    infrafamily = "infrafamily"
    infragenus = "infragenus"
    infraspecies = "infraspecies"
    modified = "modified"
    name_status = "name status"
    published = "published"
    published_in = "published in"
    publishing_author = "publishing author"
    rank = "rank"
    scientific_name = "scientific name"
    species = "species"
    species_author = "species author"
    version = "version"

class Author(Enum):
    forename = "author forename"
    full_name = "author name"
    standard_form = "author std"
    surname = "author surname"

class Publication(Enum):
    standard_form = "publication std"
    bph_number = "bph number"
    date = "date"
    isbn = "isbn"
    issn = "issn"
    lc_number = "lc number"
    preceded_by = "preceded by"
    superceded_by = "superceded by"
    title = "publication title"
    tl2_author = "tl2 author"
    tl2_number = "tl2 number"

class Filters(Enum):
    familial = {"kew":"f_familial", "col":"getFamiliesByFamilyName", "tropicos":"Search"}
    infrafamilial = {"kew":"f_infrafamilial", "tropicos":"Search"}
    generic = {"kew":"f_generic", "col":"getSpeciesByScientificName", "tropicos":"Search"}
    infrageneric = {"kew":"f_infrageneric", "tropicos":"Search"}
    specific = {"kew":"f_specific", "col":"getSpeciesByScientificName", "tropicos":"Search"}
    infraspecific = {"kew":"f_infraspecific", "col":"getSpeciesByScientificName", "tropicos":"Search"}
    commonname = {"col":"getSpeciesByCommonName", "tropicos":"Search"}
    acceptedname = {"tropicos": 'AcceptedNames'}
    synonyms = {"tropicos": "Synonyms"}
    distributions = {"tropicos": "Distributions"}
    references = {"tropicos": "References"}
    images = {"tropicos": "Images"}
    highertaxa = {"tropicos": "HigherTaxa"}
    specimens = {"tropicos": "Specimens"}
    chromosome = {"tropicos": "ChromosomeCounts"}

