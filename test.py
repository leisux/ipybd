from jsonschema import validate

my_schema = {
  "type": "object",
  "title": "Occurence Record Object Of NOI",
  "description": "Must Be One Record One Species, The Record Can Be From PreservedSpecimen, Literature, LivingSpecimen, FossilSpecimen, MaterialSample, HumanObservation, MachineObservation And So On",
  "properties": {
    "Occurence": {
      "type": "object",
      "properties": {
        "occurrenceID": {
          "type": "string",
          "pattern": "[A-Z]+:[FLA]?[0-9]+",
          "minLength": 5,
          "maxLength": 14,
          "description": "like KUN:L1245789"
        },
        "catalogNumber": {
          "type": "string",
          "minLength": 4,
          "maxLength": 10,
          "description": "L1245789"
        },
        "otherCatalogNumbers": {
          "type": "string"
        },
        "recordedBy": {
          "type": "string"
        },
        "recordNumber": {
          "type": "string"
        },
        "individualCount": {
          "type": "integer"
        },
        "sex": {
          "type": "string",
          "enum": [
            "female",
            "male"
          ]
        },
        "lifeStage": {
          "type": "string"
        },
        "behavior": {
          "type": "string"
        },
        "establishmentMeans": {
          "type": "string",
          "enum": [
            "native",
            "introduced",
            "naturalised",
            "invasive",
            "managed"
          ]
        },
        "preparations": {
          "type": "string"
        },
        "disposition": {
          "type": "string",
          "enum": [
            "in collection",
            "missing",
            "voucher elsewhere",
            "duplicates elsewhere"
          ]
        },
        "associatedMedia": {
          "type": "object",
          "properties": {
            "image": {
              "type": "array",
              "items": {
                "type": "string",
                "format": "uri",
                "pattern": "^https?://.+"
              }
            },
            "video": {
              "type": "array",
              "items": {
                "type": "string",
                "format": "uri",
                "pattern": "^https?://.+"
              }
            },
            "audio": {
              "type": "array",
              "items": {
                "type": "string",
                "format": "uri",
                "pattern": "^https?://.+"
              }
            }
          }
        },
        "associatedReferences": {
          "type": "array",
          "items": {
            "type": "string",
            "format": "uri",
            "pattern": "^https?://.+"
          }
        },
        "associatedSequences": {
          "type": "array",
          "items": {
            "type": "string",
            "format": "uri",
            "pattern": "^https?://.+"
          }
        },
        "occurrenceRemarks": {
          "type": "string"
        }
      },
      "required": [
        "recordedBy"
      ]
    },
    "Event": {
      "type": "object",
      "properties": {
        "eventDate": {
          "type": "string",
          "format": "date-time"
        },
        "habitat": {
          "type": "string"
        },
        "fieldNumber": {
          "type": "string"
        },
        "samplingProtocol": {
          "type": "string"
        },
        "fieldNotes": {
          "type": "string"
        },
        "fundedBy": {
          "type": "string"
        }
      },
      "required": [
        "eventDate"
      ]
    },
    "Location": {
      "type": "object",
      "properties": {
        "country": {
          "type": "string"
        },
        "countryCode": {
          "type": "string",
          "description": "Recommended best practice is to use an ISO 3166-1-alpha-2 country code. like CN",
          "minLength": 2,
          "maxLength": 3
        },
        "province": {
          "type": "string"
        },
        "city": {
          "type": "string"
        },
        "county": {
          "type": "string"
        },
        "locality": {
          "type": "string"
        },
        "minimumElevationInMeters": {
          "type": "number",
          "minimum": -800,
          "maximum": 8845
        },
        "maximumElevationInMeters": {
          "type": "number",
          "minimum": -800,
          "maximum": 8845
        },
        "minimumDepthInMeters": {
          "type": "number",
          "minimum": 0,
          "maximum": 12000
        },
        "maximumDepthInMeters": {
          "type": "number",
          "minimum": 0,
          "maximum": 12000
        },
        "minimumDistanceAboveSurfaceInMeters": {
          "type": "number",
          "minimum": -12000,
          "maximum": 8845
        },
        "maximumDistanceAboveSurfaceInMeters": {
          "type": "number",
          "minimum": -12000,
          "maximum": 8845
        }
      },
      "required": [
        "country"
      ]
    },
    "Identification": {
      "type": "object",
      "additionalProperties": {
        "type": "array",
        "items": {
          "type": "object",
          "properties": {
            "scientificName": {
              "type": "string",
              "pattern": "[A-Z][a-z][a-z]+"
            },
            "identifiedBy": {
              "type": "string"
            },
            "dateIdentified": {
              "type": "string",
              "format": "date-time"
            },
            "typeStatus": {
              "type": "string",
              "enum": [
                "Type",
                "Type species",
                "Type genus",
                "Allolectotype",
                "Alloneotype",
                "Allotype",
                "Cotype",
                "Epitype",
                "Ex-epitype",
                "Ex-holotype",
                "Ex-isotype",
                "Ex-lectotype",
                "Ex-neotype",
                "Ex-paratype",
                "Ex-syntype",
                "Ex-type",
                "Hapantotype",
                "Holotype",
                "Iconotype",
                "Isolectotype",
                "Isoneotype",
                "Isosyntype",
                "Isotype",
                "Lectotype",
                "Neotype",
                "Paralectotype",
                "Paraneotype",
                "Paratype",
                "Plastoholotype",
                "Plastoisotype",
                "Plastolectotype",
                "Plastoneotype",
                "Plastoparatype",
                "Plastosyntype",
                "Plastotype",
                "Secondary type",
                "Supplementary type",
                "Syntype",
                "Topotype",
                "Original material",
                "Not type"
              ]
            }
          }
        }
      },
      "propertyNames": {
        "type": "string",
        "pattern": "[A-Z]+",
        "minLength": 1,
        "maxLength": 5
      }
    },
    "Record": {
      "type": "object",
      "properties": {
        "basisOfRecord": {
          "type": "string",
          "enum": [
            "PreservedSpecimen",
            "Literature",
            "LivingSpecimen",
            "FossilSpecimen",
            "MaterialSample",
            "HumanObservation",
            "MachineObservation",
            "Unknow"
          ]
        },
        "rights": {
          "type": "string"
        },
        "rightsHolder": {
          "type": "string"
        },
        "licence": {
          "type": "string",
          "enum": [
            "CC0 1.0",
            "CC BY 4.0",
            "CC BY-NC 4.0",
            "Unspecified"
          ]
        },
        "modified": {
          "type": "string",
          "format": "date-time"
        },
        "references": {
          "type": "object",
          "additionalProperties": {
            "type": "string",
            "format": "uri",
            "pattern": "^https?://.+"
          }
        },
        "apiData": {
          "type": "object",
          "additionalProperties": {
            "type": "string",
            "format": "uri",
            "pattern": "^https?://.+"
          }
        },
        "thumbnails": {
          "type": "object",
          "additionalProperties": {
            "type": "string",
            "format": "uri",
            "pattern": "^https?://.+"
          }
        },
        "institutionCode": {
          "type": "string"
        },
        "dynamicProperties": {
          "type": "object"
        }
      },
      "required": [
        "basisOfRecord",
        "rights",
        "rightsHolder",
        "licence"
      ]
    }
  },
  "required": [
    "Occurence",
    "Event",
    "Record"
  ]
}


json_data = {
    "Occurence":{
        "occurrenceID":"KUN:1206578",
        "catalogNumber":"1206578",
        "otherCatalogNumbers":"657894",
        "recordedBy":"徐洲锋,刘恩德,魏志丹",
        "recordedNumber":"LED7896",
        "individualCount":3,
        "lifeStage":"有花无果",
        "establishmentMeans":"invasive",
        "preparations":"腊叶标本",
        "disposition":"missing",
        "associatedMedia":{
            "images":[
                "https://img.cc0.cn/d/file/20191017/7eb3706e1e0e878d8bca1f7180fa8831.jpg/content",
                "https://img.cc0.cn/d/file/20191017/7eb3706e1e0e878d8bca1f7180fa8831.jpg/content"
            ],
            "videos":[
                "https://img.cc0.cn/d/file/20191017/7eb3706e1e0e878d8bca1f7180fa8831.jpg/content",
                "https://img.cc0.cn/d/file/20191017/7eb3706e1e0e878d8bca1f7180fa8831.jpg/content"

            ],
            "audios":[
                "https://img.cc0.cn/d/file/20191017/7eb3706e1e0e878d8bca1f7180fa8831.jpg/content",
                "https://img.cc0.cn/d/file/20191017/7eb3706e1e0e878d8bca1f7180fa8831.jpg/content"
            ]
        },
        "associatedSequences":[
            "http://www.ncbi.nlm.nih.gov/nuccore/U34853.1",
            "http://www.ncbi.nlm.nih.gov/nuccore/GU328060",
            "http://www.ncbi.nlm.nih.gov/nuccore/AF326093"
        ],
        "associatedReferences":[
            "http://www.sciencemag.org/cgi/content/abstract/322/5899/261"
        ]
    },
    "Event":{
        "eventDate":"2020-12-23 12:31:54",
        "habitat":"距湖边300m的松林内。",
        "fundedBy":"QTP 植物多样性调查"
    },
    "Location":{
        "country": "中国",
        "countryCode":"CN",
        "province":"云南省",
        "city":"昆明市",
        "locality":"松华坝水库",
        "minimumElevationInMeters":2615,
        "maximumElevationInMeters":3456.67
    },
    "Identification": {
        "KUN": [
            {
                "scientificName": "Rho",
                "identifiedBy": "徐洲锋",
                "dateIdentified": "2012-12-3"
            },
            {
                "scientificName": "Rhododendron sinsis Smith.",
                "identifiedBy": "刘恩德",
                "dateIdentified": "2012-12-30 08:23:45"
            }
        ],
        "CVH": [
            {
                "scientificName": "Rhododendron delavayi Smith.",
                "identifiedBy": "徐洲锋",
                "dateIdentified": "2012-12-30 12:23:45"
            },
            {
                "scientificName": "Rhododendron sinsis Smith.",
                "identifiedBy": "刘恩德",
                "dateIdentified": "2012-12-30 08:23:45"
            }
        ]
    },
    "Record":{
        "basisOfRecord":"PreservedSpecimen",
        "rights":"刘恩德",
        "rightsHolder":"KUN",
        "licence":"CC BY 4.0",
        "modified":"2019-12-23 12:23:35",
        "references":{
            "KUN":"http://kun.kingdonia.org/speciman/newshow/tpl/2/id/165193",
            "CVH":"http://www.cvh.ac.cn/spms/info.php?id=c0724246"
        },
        "apiData":{
            "KUN":"http://www.sp2000.org.cn/api/v2/getSpeciesByFamilyId?apiKey=42ad0f57ae46407686d1903fd44aa34c&familyId=F20171000000256&page=2",
            "CVH":"http://beta.ipni.org/api/1/search?perPage=500&cursor=%2A&q=Thalictrum+aquilegiifolium+var.+sibiricum&f=f_infraspecific"
        },
        "thumbnails":{
            "KUN":"http://www.sp2000.org.cn/api/v2/getSpeciesByFamilyId?apiKey=42ad0f57ae46407686d1903fd44aa34c&familyId=F20171000000256&page=2",
            "CVH":"http://beta.ipni.org/api/1/search?perPage=500&cursor=%2A&q=Thalictrum+aquilegiifolium+var.+sibiricum&f=f_infraspecific"
        },
        "institutionCode":"KUN",
        "dynamicProperties":{"flower":"粉红色", "stem":"树皮粗糙有绿白色裂纹", "频度":5}

    }
}


if __name__ == "__main__":
    validate(instance=json_data, schema=my_schema)
