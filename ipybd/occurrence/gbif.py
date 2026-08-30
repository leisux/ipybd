import pandas as pd
import os

path = r"/Users/xuzhoufeng/Downloads/0077375-240506114902167"
media_path = os.path.join(path, 'multimedia.txt')
occurrence_path = os.path.join(path, 'occurrence.txt')
result_path = os.path.join(path, 'occurrence.xlsx')

media = pd.read_table(media_path, dtype=str)
occurrence = pd.read_table(occurrence_path, dtype=str)

media = media[['gbifID', 'identifier', 'references', 'source', 'audience', 'creator', 'license', 'rightsHolder']]
occurrence = occurrence[['gbifID','rightsHolder', 'publisher', 'license', 'basisOfRecord', 'references',
 'bibliographicCitation', 'occurrenceID', 'institutionCode', 'collectionCode', 'catalogNumber', 'recordNumber', 
 'fieldNumber', 'recordedBy', 'individualCount', 'lifeStage', 'occurrenceRemarks', 'fieldNotes', 
 'eventDate', 'habitat', 'countryCode', 'stateProvince', 'county', 'municipality', 'locality', 'verbatimLocality',
 'decimalLatitude', 'decimalLongitude', 'elevation', 'verbatimElevation', 'georeferenceProtocol', 'kingdom', 'scientificName', 'identifiedBy', 
 'dateIdentified', 'typeStatus', 'modified']]

table = pd.merge(occurrence, media, how='left', on='gbifID')

with pd.ExcelWriter(result_path, engine='openpyxl') as writer:
    table.to_excel(writer, sheet_name='Sheet1')