schema={
  "type": "object",
  "title": "Occurence Record Object Of NOI",
  "description": "Must Be One Record One Species, The Record Can Be From PreservedSpecimen, Literature, LivingSpecimen, FossilSpecimen, MaterialSample, HumanObservation, MachineObservation And So On",
  "properties": {
    "Occurrence": {
      "title_cn": "发生记录",
      "type": "object",
      "properties": {
        "occurrenceID": {
          "title_cn": "机构标识",
          "type": "string",
          "pattern": "[A-Za-z0-9:-]+",
          "minLength": 5,
          "maxLength": 45,
          "description": "like KUN:L1245789"
        },
        "catalogNumber": {
          "title_cn": "资源编号",
          "type": "string",
          "pattern": "[A-Za-z0-9]+",
          "minLength": 2,
          "maxLength": 35,
          "description": "L1245789"
        },
        "otherCatalogNumbers": {
          "title_cn": "其他编号",
          "type": "string"
        },
        "recordedBy": {
          "title_cn": "记录人员",
          "type": "array",
          "items": {
            "type": "string"
          }
        },
        "recordNumber": {
          "title_cn": "记录编号",
          "type": "string"
        },
        "individualCount": {
          "title_cn": "数量",
          "type": "integer"
        },
        "sex": {
          "title_cn": "性别",
          "type": "string",
          "enum": [
            "♂",
            "♀",
            "☉"
          ]
        },
        "lifeStage": {
          "title_cn": "生命阶段",
          "type": "string",
          "enum": [
            "无花无果",
            "有花无果",
            "无花有果",
            "有花有果",
            "无孢子囊",
            "有孢子囊",
            "幼",
            "亚成",
            "成",
            "不清"
          ]
        },
        "behavior": {
          "title_cn": "行为",
          "type": "string"
        },
        "establishmentMeans": {
          "title_cn": "定居性质",
          "type": "string",
          "enum": [
            "本土",
            "引种",
            "归化",
            "入侵",
            "受控"
          ]
        },
        "preparations": {
          "title_cn": "处理方式",
          "type": "string"
        },
        "disposition": {
          "title_cn": "存放状态",
          "type": "string",
          "enum": [
            "在库",
            "出库",
            "遗失"
          ]
        },
        "associatedMedia": {
          "title_cn": "关联媒体",
          "type": "array",
          "items": {
            "type": "string",
            "format": "uri"
          }
        },
        "associatedReferences": {
          "title_cn": "关联文献",
          "type": "array",
          "items": {
            "type": "string",
            "format": "uri"
          }
        },
        "associatedSequences": {
          "title_cn": "关联序列",
          "type": "array",
          "items": {
            "type": "string",
            "format": "uri"
          }
        },
        "occurrenceRemarks": {
          "title_cn": "发生备注",
          "type": "string"
        }
      },
      "required": [
        "occurrenceID",
        "recordedBy"
      ]
    },
    "Event": {
      "title_cn": "事件",
      "type": "object",
      "properties": {
        "eventDate": {
          "title_cn": "发生日期",
          "type": "string",
          "format": "date-time"
        },
        "habitat": {
          "title_cn": "栖息环境",
          "type": "string"
        },
        "fieldNumber": {
          "title_cn": "事件编号",
          "type": "string"
        },
        "samplingProtocol": {
          "title_cn":"样品获取方式",
          "type": "string"
        },
        "fieldNotes": {
          "title_cn": "事件备注",
          "type": "string"
        },
        "fundedBy": {
          "title_cn": "工作资助",
          "type": "string"
        }
      }
    },
    "Location": {
      "title_cn": "位置",
      "type": "object",
      "properties": {
        "country": {
          "title_cn": "国家",
          "type": "string"
        },
        "countryCode": {
          "title_cn": "国家编码",
          "type": "string",
          "description": "Recommended best practice is to use an ISO 3166-1-alpha-2 country code. like CN",
          "minLength": 2,
          "maxLength": 3
        },
        "province": {
          "title_cn": "省/自治区",
          "type": "string"
        },
        "city": {
          "title_cn": "市/州",
          "type": "string"
        },
        "county": {
          "title_cn": "区/县",
          "type": "string"
        },
        "locality": {
          "title_cn": "具体地点",
          "type": "string"
        },
        "decimalLatitude": {
          "title_cn": "纬度",
          "type":"number",
          "minimum":-90,
          "maximum":90
        },
        "decimalLongitude":{
          "title_cn": "经度",
          "type":"number",
          "minimum":-180,
          "maximum":180
        },
        "geodeticDatum":{
          "title_cn": "地理坐标系",
          "type":"string",
          "Enum":[
            "WGS84",
            "CGCS2000",
            "BD09",
            "GCJ-02",
            "Beijing 1954",
            "Xian 1980",
            "EPSG:4326",
            "NAD27",
            "Campo Inchauspe",
            "European 1950",
            "Clarke 1866",
            "Unknown"
          ]
        },
        "georeferenceProtocol":{
          "title_cn": "地理位置确定方式",
          "type": "string"
        },
        "minimumElevationInMeters": {
          "title_cn": "海拔/海拔低值",
          "type": "number",
          "minimum": -800,
          "maximum": 8845
        },
        "maximumElevationInMeters": {
          "title_cn": "海拔高值",
          "type": "number",
          "minimum": -800,
          "maximum": 8845
        },
        "verbatimElevation": {
          "title_cn": "原始海拔记录",
          "type": "string"
        },
        "minimumDepthInMeters": {
          "title_cn": "深度/最小深度",
          "type": "number",
          "minimum": 0,
          "maximum": 12000
        },
        "maximumDepthInMeters": {
          "title_cn": "最大深度",
          "type": "number",
          "minimum": 0,
          "maximum": 12000
        },
        "minimumDistanceAboveSurfaceInMeters": {
          "title_cn": "相对距离/最小相对距离",
          "type": "number",
          "minimum": -12000,
          "maximum": 8845
        },
        "maximumDistanceAboveSurfaceInMeters": {
          "title_cn": "最大相对距离",
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
      "title_cn": "鉴定",
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "vernacularName":{
            "title_cn": "中文名",
            "type":"string"
          },
          "scientificName": {
            "title_cn": "学名",
            "type": "string",
            "pattern": "[A-Z][a-z][a-z]+"
          },
          "identifiedBy": {
            "title_cn": "鉴定人",
            "type": "string"
          },
          "dateIdentified": {
            "title_cn": "鉴定日期",
            "type": "string",
            "format": "date-time"
          },
          "typeStatus": {
            "title_cn": "模式等级",
            "type": "string",
            "enum": [
              "type",
              "type species",
              "type genus",
              "allolectotype",
              "alloneotype",
              "allotype",
              "cotype",
              "epitype",
              "ex-epitype",
              "ex-holotype",
              "ex-isotype",
              "ex-lectotype",
              "ex-neotype",
              "ex-paratype",
              "ex-syntype",
              "ex-type",
              "hapantotype",
              "holotype",
              "iconotype",
              "isolectotype",
              "isoneotype",
              "isosyntype",
              "isotype",
              "lectotype",
              "neotype",
              "paralectotype",
              "paraneotype",
              "paratype",
              "plastoholotype",
              "plastoisotype",
              "plastolectotype",
              "plastoneotype",
              "plastoparatype",
              "plastosyntype",
              "plastotype",
              "secondary type",
              "supplementary type",
              "syntype",
              "topotype",
              "original material",
              "not type"
            ]
          }
        }
      }
    },
    "Record": {
      "title_cn": "记录",
      "type": "object",
      "properties": {
        "category": {
          "title_cn": "类别",
          "type": "string",
          "enum": [
            "植物",
            "动物",
            "真菌",
            "假菌",
            "古细菌",
            "原核生物",
            "病毒"
          ]
        },
        "datasetName": {
          "title_cn": "所属数据集",
          "type": "string"
        },
        "basisOfRecord": {
          "title_cn": "记录依据",
          "type": "string",
          "enum": [
            "生物痕迹",
            "人类观察",
            "机器记录",
            "馆藏标本",
            "活体标本",
            "化石标本",
            "文献记录",
            "不清"
          ]
        },
        "rightsHolder": {
          "title_cn": "版权所有",
          "type": "string"
        },
        "dataFrom": {
          "title_cn": "数据来源",
          "type": "string"
        },
        "license": {
          "title_cn": "许可协议",
          "type": "string",
          "format":"uri"
        },
        "modified": {
          "title_cn": "修改日期",
          "type": "string",
          "format": "date-time"
        },
        "references": {
          "title_cn": "源数据页面",
          "type": "string",
          "format": "uri"
        },
        "dataApi": {
          "title_cn": "源数据接口",
          "type": "string",
          "format": "uri"
        },
        "thumbnails": {
          "title_cn": "缩略图",
          "type": "string",
          "format": "uri"
        },
        "institutionCode": {
          "title_cn": "机构代码",
          "type": "string"
        },
        "collectionCode":{
          "title_cn": "馆藏代码",
          "type": "string"
        }
      },
      "required": [
        "basisOfRecord",
        "dataFrom",
        "rightsHolder",
        "license"
      ]
    }
  },
  "required": [
    "Occurrence",
    "Location",
    "Record"
  ]
}
