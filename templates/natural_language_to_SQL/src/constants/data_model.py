table_descriptions = [
  {
    "TableName": "HC_Patient_Daily_Summary_v3",
    "Description": "This table aggregates comprehensive daily records for patients by combining healthcare data, demographic attributes, insurance information, and monitoring metrics. It includes columns for dates, patient and provider identifiers, insurance details (plans, coverage tiers, patient types), demographic data (age, activation dates), health metrics (chronic conditions, active prescriptions), device performance (uptime, inactive hours, resets), and various monitoring indices (wellness, vital signs, activity). Use this table to analyze daily patient health status, evaluate monitoring effectiveness, and study insurance coverage patterns. Relationships: It contains three foreign keys—'INSURANCE_REC.ZIP_CODE' (references D_HC_Geography_v3.ZIP_CODE), 'INSURANCE_REC.PATIENT_TYPE_ID' (references D_Patient_Type_v3.PATIENT_TYPE_ID), and 'INSURANCE_REC.INSURANCE_PLAN_ID' (references D_Insurance_Plan_v3.PLAN_ID)."
  },
  {
    "TableName": "HC_Patient_Device_Details_v3",
    "Description": "This table records detailed information about the medical devices used by patients on a daily basis. It includes columns for patient identifiers, device specifics (ID, OS, brand, model, type), device characteristics (category, connectivity, power source, FDA approval status), technical specifications (accuracy, maintenance schedules), and usage metrics (active hours, reading counts). Use this table to analyze device utilization, performance, and reliability across different patient populations. Relationships: It contains two foreign keys—'PATIENT_ID' (references HC_Patient_Daily_Summary_v3.PATIENT_ID) and 'PROVIDER_ID' (references D_HC_Providers_v3.PROVIDER_ID)."
  },
  {
    "TableName": "HC_Patient_Medication_Summary_v3",
    "Description": "This table captures comprehensive daily medication usage and adherence data for patients. It includes columns for patient and provider identifiers, medication details (IDs, names, strength, form), prescription information (frequency, route, start/end dates), adherence metrics (rates, doses taken/missed), and cost data (insurance coverage, patient costs). Use this table to analyze medication compliance patterns, evaluate cost effectiveness, and identify adherence trends. Relationships: It contains three foreign keys—'PATIENT_ID' (references HC_Patient_Daily_Summary_v3.PATIENT_ID), 'PROVIDER_ID' (references D_HC_Providers_v3.PROVIDER_ID), and 'MEDICATION_PRESCRIBED_BY' (references D_HC_Providers_v3.PROVIDER_ID)."
  },
  {
    "TableName": "D_Patient_Type_v3",
    "Description": "This table classifies patients according to various organizational and care management criteria. It includes columns for patient type identifiers, descriptive names, grouping IDs, length-of-stay parameters, and facility requirement indicators. Use this table to segment patient populations, support care planning, and analyze resource requirements across different patient categories. Note: This table serves as a reference dimension and is referenced by HC_Patient_Daily_Summary_v3 via the foreign key 'INSURANCE_REC.PATIENT_TYPE_ID'."
  },
  {
    "TableName": "D_Insurance_Plan_v3",
    "Description": "This table details the health insurance plans available to patients, including coverage types, network information, and cost structures. It describes plan identifiers, names, service coverages (primary care, specialists, emergency, prescriptions, etc.), financial terms (deductibles, copays, out-of-pocket maximums), and validity periods. Use this table to evaluate insurance offerings, support benefit analysis, and understand plan attributes. Relationships: It includes the foreign key 'INSURER_ID' which references D_HC_Insurers_v3.INSURER_ID. It is also referenced by HC_Patient_Daily_Summary_v3 via the foreign key 'INSURANCE_REC.INSURANCE_PLAN_ID'."
  },
  {
    "TableName": "D_HC_Geography_v3",
    "Description": "This table provides detailed geographical and healthcare accessibility information for service areas. It includes ZIP code identifiers, location names (city, county, state), geographic coordinates, demographic statistics (population, median age, household income), healthcare resource metrics (facility counts, physician counts, bed availability), and accessibility indicators (travel times, shortage designations, broadband access). Use this table for geographic analysis of healthcare access, resource distribution studies, and demographic profiling. Note: It is referenced by HC_Patient_Daily_Summary_v3 via the foreign key 'INSURANCE_REC.ZIP_CODE'."
  },
  {
    "TableName": "D_HC_Procedures_v3",
    "Description": "This table catalogs medical procedures with detailed attributes including procedural codes, descriptions, complexity levels, and associated specialties. It includes procedure identifiers, categorizations, specialty associations, risk/complexity assessments, duration estimates, preparation requirements, facility settings, and cost information. Use this table to analyze procedure patterns, estimate resource needs, and evaluate cost structures across different medical interventions. Note: This table serves as a reference dimension for procedure-related analysis."
  },
  {
    "TableName": "D_HC_Providers_v3",
    "Description": "This table contains comprehensive information about healthcare providers including specialties, locations, and network affiliations. It includes provider identifiers, type classifications, contact details, location information, credential data (NPI numbers, years in practice, certifications), service offerings (telehealth availability, language support), and quality ratings. Use this table to analyze provider distributions, network adequacy, and service accessibility. Relationships: It includes the foreign key 'ZIP_CODE' which references D_HC_Geography_v3.ZIP_CODE. It is also referenced by HC_Patient_Device_Details_v3 and HC_Patient_Medication_Summary_v3 via their respective 'PROVIDER_ID' foreign keys."
  },
  {
    "TableName": "D_Patient_Devices_v3",
    "Description": "This table maintains an inventory of patient devices with technical and status information. It includes patient and device identifiers, device specifications (type, manufacturer, model, serial number), lifecycle data (purchase date, firmware version), operational status (battery level, last sync time), and location information. Use this table to track device inventory, monitor device status, and manage device maintenance requirements. Relationships: It contains the foreign key 'PATIENT_ID' which references D_Patients_v3.PATIENT_ID."
  }
]


json_rules = """
  "rules": [
    {{
      "id": "HC1",
      "name": "Chronic Condition Filtering",
      "condition": "Look for patients with chronic conditions in the question '{question}'.",
      "action": "When the question mentions chronic conditions, use 'INSURANCE_REC.CHRONIC_CONDITIONS_NUM > 0' as a filter. For specific thresholds mentioned in the question, use that value instead."
    }},
    {{
      "id": "HC2",
      "name": "Device Activity Tracking",
      "condition": "Check if the question '{question}' is asking for analysis of device usage or effectiveness.",
      "action": "Consider using 'DEVICE_REC.DEVICE_INACTIVE_HOURS < 12' for active devices, but only apply this filter when device activity is explicitly relevant to the query."
    }},
    {{
      "id": "HC3",
      "name": "Telehealth Patients",
      "condition": "Look for telehealth users or remote care patients in the question '{question}'.",
      "action": "For telehealth-related queries, use 'INSURANCE_REC.PRIMARY_CARE_TECHNOLOGY_ID = 'TeleHealth'' or similar constraints as appropriate."
    }},
    {{
      "id": "HC4",
      "name": "High-Risk Patients",
      "condition": "You are asked about high-risk patients in the question '{question}'.",
      "action": "For high-risk queries, consider using either 'HEALTH_REC.ELEVATED_RISK_PERCENTAGE > 0.5' or 'HEALTH_REC.OVERALL_HEALTH_INDEX < 70' but not both unless specifically required."
    }},
    {{
      "id": "HC5",
      "name": "Medication Adherence Categories",
      "condition": "The question '{question}' asks about medication adherence levels or categories.",
      "action": "When querying medication adherence, prefer the categorical 'ADHERENCE_LEVEL' field over the numeric 'ADHERENCE_RATE' when appropriate."
    }},
    {{
      "id": "HC6",
      "name": "Patient Age Grouping",
      "condition": "You are using the field 'INSURANCE_REC.PATIENT_AGE_NUM' in the query.",
      "action": "For demographic analysis, consider using 'INSURANCE_REC.PATIENT_AGE_GROUP_CD' for consistent grouping, but either field is acceptable."
    }},
    {{
      "id": "HC7",
      "name": "Wearable Device Filtering",
      "condition": "Look for information on wearable devices in the question '{question}'.",
      "action": "For wearable device queries, use 'DEVICE_CATEGORY = 'Wearable'' if appropriate. Additional wearable-specific metrics can be found in the 'MONITORING_REC.WEARABLE_REC' fields."
    }},
    {{
      "id": "HC8",
      "name": "Patient Count Calculation",
      "condition": "You are asked to count the number of patients in the question '{question}'.",
      "action": "For patient counting, use 'COUNT(DISTINCT PATIENT_ID)' to avoid duplication."
    }},
    {{
      "id": "HC9",
      "name": "Device Battery Level",
      "condition": "The question '{question}' mentions device battery or power levels.",
      "action": "For battery-related queries, you can use 'DEVICE_BATTERY_LEVEL < 25' for low battery (below 25%) or modify the threshold as needed."
    }},
    {{
      "id": "HC10",
      "name": "Health Index Interpretation",
      "condition": "The query references health index fields.",
      "action": "Health index values range from 0-100 with higher values indicating better health. General interpretations: 90+ 'Excellent', 75-89 'Good', 60-74 'Fair', <60 'Concerning'."
    }},
    {{
      "id": "HC11", 
      "name": "Recent Activity Timeframe",
      "condition": "The question '{question}' asks about recent activity or mentions a timeframe like 'last month'.",
      "action": "When a specific timeframe is mentioned, use an appropriate date filter like 'DATE_RECORDED >= DATE('now', '-30 days')' for 'last month' or adjust the interval as needed."
    }}
  ]
"""


global_database_model = [
  {
    "TableName": "HC_Patient_Daily_Summary_v3",
    "Description": "Entity that collects the information associated with the patient health data on a daily basis, and combines it with demographic features and insurance coverage.",
    "Columns": [
      {
        "ColumnName": "RECORD_DATE",
        "DataType": "VARCHAR",
        "Description": "Year, month and day of the data. Format: YYYY-MM-DD (4 digits for year, months from 01 to 12, days from 01 to 31). Example values: '2023-04-24', '2024-09-16', '2022-06-01'"
      },
      {
        "ColumnName": "PATIENT_ID",
        "DataType": "VARCHAR",
        "Description": "Unique Identifier of the patient within the healthcare system. Format: String. Example values: '164559592362680187', '-6149090817956898776'"
      },
      {
        "ColumnName": "PROVIDER_ID",
        "DataType": "VARCHAR",
        "Description": "Identifier of the healthcare provider (within the network of providers), codified according to the IDs defined in 'D_Provider' entity. Format: String. Example values: '0401', '0403'"
      },
      {
        "ColumnName": "USER_PORTAL_ID",
        "DataType": "VARCHAR",
        "Description": "Unique identifier of the user (data owner) in the Patient Portal platform. Format: String. Example values: '3706277557884218994', '-6189348075566519429'"
      },
      {
        "ColumnName": "PHONE_NUMBER",
        "DataType": "VARCHAR",
        "Description": "Phone number of the patient, with international prefix. Format: Phone number in ITU E.164 format, including the International prefix starting with '+'. Example values: '+14155552671', '+442071838750'"
      },
      {
        "ColumnName": "INSURANCE_REC.MONTH_DT",
        "DataType": "VARCHAR",
        "Description": "Year and month of the insurance data. Format: YYYY-MM-DD (4 digits for year, months from 01 to 12, DD=01). Example values: '2023-04-01', '2024-05-01', '2022-06-01'"
      },
      {
        "ColumnName": "INSURANCE_REC.POLICY_ID",
        "DataType": "VARCHAR",
        "Description": "Unique identifier of the insurance policy. Format: String. Example values: '-35271880464624184', '4840798815685406415'"
      },
      {
        "ColumnName": "INSURANCE_REC.INSURANCE_PLAN_ID",
        "DataType": "VARCHAR",
        "Description": "Unique identifier of the insurance plan subscribed by the patient. Insurance plans, along with their identifiers, are defined in the table 'D_Insurance_Plan'. Format: String."
      },
      {
        "ColumnName": "INSURANCE_REC.COVERAGE_TIER_ID",
        "DataType": "VARCHAR",
        "Description": "Code that identifies the coverage tier subscribed by the patient. Coverage tiers, along with their identifiers, are defined in the table 'D_Insurance_Plan'. Format: String consisting of a sequence of numeric codes separated by characters '-' or '='. Example values: '-1', '391==6-16-19', '1415==6-1302-19'"
      },
      {
        "ColumnName": "INSURANCE_REC.ZIP_CODE",
        "DataType": "VARCHAR",
        "Description": "Identifier of the geographical area assigned to the patient (typically the geographical area of the patient home). Format: alphanumeric string. Example values: '94107', '10023', '60601'"
      },
      {
        "ColumnName": "INSURANCE_REC.PATIENT_TYPE_ID",
        "DataType": "VARCHAR",
        "Description": "Organizational patient type classification. Format: two letter string. Possible values: 'IN' - Inpatient, 'OP' - Outpatient, 'ED' - Emergency Department, 'AM' - Ambulatory, 'IC' - Intensive Care, 'LC' - Long-term Care, 'SC' - Specialty Care, 'PC' - Primary Care, 'CH' - Children, 'OT' - Other"
      },
      {
        "ColumnName": "INSURANCE_REC.PRIMARY_CARE_TECHNOLOGY_ID",
        "DataType": "VARCHAR",
        "Description": "Technology type used for primary care visits. Format: String. Exact enumerated values: 'In-Person', 'TeleHealth', 'Hybrid', 'Remote'"
      },
      {
        "ColumnName": "INSURANCE_REC.SPECIALIST_TECHNOLOGY_ID",
        "DataType": "VARCHAR",
        "Description": "Technology type used for specialist care visits. Format: String. Exact enumerated values: 'In-Person', 'TeleHealth', 'Hybrid', 'Remote'"
      },
      {
        "ColumnName": "INSURANCE_REC.MONITORING_TECHNOLOGY_ID",
        "DataType": "VARCHAR",
        "Description": "Technology type used for patient monitoring. Format: String. Exact enumerated values: 'Clinic', 'Remote', 'Wearable', 'Implanted'"
      },
      {
        "ColumnName": "INSURANCE_REC.PREMIUM_AMOUNT",
        "DataType": "FLOAT",
        "Description": "Monthly premium amount (USD) of the insurance plan. Format: Float. Example values: 450.0, 1200.0"
      },
      {
        "ColumnName": "INSURANCE_REC.PRIMARY_PROVIDER_IND",
        "DataType": "BOOLEAN",
        "Description": "Indicator that identifies whether this is the patient's primary provider"
      },
      {
        "ColumnName": "INSURANCE_REC.MULTI_PROVIDER_IND",
        "DataType": "VARCHAR",
        "Description": "It is an enumeration of values to classify the patient according to the type of providers they use. It allows to define the patient as having 'Single' (only one provider), 'Dual' (two providers), or 'Multiple' (more than two providers)."
      },
      {
        "ColumnName": "INSURANCE_REC.PATIENT_AGE_NUM",
        "DataType": "INT",
        "Description": "Age of the patient measured in years. Value 0 corresponds to less than 1 year. Format: Integer. Example values: 0, 24, 56"
      },
      {
        "ColumnName": "INSURANCE_REC.PATIENT_AGE_GROUP_CD",
        "DataType": "VARCHAR",
        "Description": "Code of the age segment for the patient. It is codified according to the codes defined in 'D_Age_Group' entity. Format: alphanumeric string. Example values: '0-17', '18-34', '35-50', '51-64', '65+'"
      },
      {
        "ColumnName": "INSURANCE_REC.PATIENT_ACTIVATION_DT",
        "DataType": "VARCHAR",
        "Description": "Patient registration date in system. Format: YYYY-MM-DD (4 digits for year, months from 01 to 12, days from 01 to 31)."
      },
      {
        "ColumnName": "INSURANCE_REC.PATIENT_TENURE_NUM",
        "DataType": "INT",
        "Description": "Number of months since patient registration corresponding to the month specified in the field INSURANCE_REC.MONTH_DT"
      },
      {
        "ColumnName": "INSURANCE_REC.TOTAL_CHARGES",
        "DataType": "VARCHAR",
        "Description": "Total charges, without insurance coverage, generated by the patient, and attributed to the month defined in field MONTH_DT measured in USD. Format: float value expressed in decimal string."
      },
      {
        "ColumnName": "INSURANCE_REC.CLAIMS_COUNT",
        "DataType": "FLOAT",
        "Description": "Number of insurance claims in the calendar month (corresponding to the month specified in the field INSURANCE_REC.MONTH_DT). Format: Float. Example values: 1.0, 2.0, 3.5"
      },
      {
        "ColumnName": "INSURANCE_REC.APPOINTMENTS_COUNT",
        "DataType": "FLOAT",
        "Description": "Number of appointments in the calendar month (corresponding to the month specified in the field INSURANCE_REC.MONTH_DT). Format: Float. Example values: 1.0, 2.0, 3.0"
      },
      {
        "ColumnName": "INSURANCE_REC.INITIAL_DIAGNOSIS_DT",
        "DataType": "VARCHAR",
        "Description": "Date of initial diagnosis for chronic patients. Format: Date, YYYY-MM-DD (4 digits for year, months from 01 to 12, days from 01 to 31)"
      },
      {
        "ColumnName": "INSURANCE_REC.CHRONIC_CONDITIONS_NUM",
        "DataType": "INT",
        "Description": "Number of chronic conditions diagnosed for the patient in the month specified in the field INSURANCE_REC.MONTH_DT. Format: Integer. Example values: 0,1,2."
      },
      {
        "ColumnName": "INSURANCE_REC.ACTIVE_PRESCRIPTIONS_NUM",
        "DataType": "INT",
        "Description": "Number of active prescriptions for the patient in the month specified in the field INSURANCE_REC.MONTH_DT. Format: Integer. Example values: 0,1,2."
      },
      {
        "ColumnName": "DEVICE_REC.DEVICE_UPTIME_DAYS",
        "DataType": "INT",
        "Description": "Number of days in a row that the patient's monitoring device has been active since last reset. Format: Integer. Example values: 1,2,3"
      },
      {
        "ColumnName": "DEVICE_REC.DEVICE_INACTIVE_HOURS",
        "DataType": "BIGINT",
        "Description": "Number of hours without receiving data from the patient's monitoring device in a day. Format: Integer. Possible values: integer numbers between 0 and 24. Example values: 0,1,12,24"
      },
      {
        "ColumnName": "DEVICE_REC.DEVICE_RESETS_NUM",
        "DataType": "BIGINT",
        "Description": "Number of resets of a patient's monitoring device in a day. Format: Integer. Example values: 0,1,2"
      },
      {
        "ColumnName": "DEVICE_REC.DEVICE_OFFLINE_NIGHT_IND",
        "DataType": "BOOLEAN",
        "Description": "Boolean value that is true if the patient's monitoring device has been turned off at night. Format: Boolean. Possible values: true or false."
      },
      {
        "ColumnName": "DEVICE_REC.DEVICE_MANUFACTURER",
        "DataType": "VARCHAR",
        "Description": "Manufacturer of the patient's monitoring device. Format: String."
      },
      {
        "ColumnName": "MONITORING_REC.SENSORS_REC.SENSORS_INACTIVE_HOURS",
        "DataType": "BIGINT",
        "Description": "Number of hours without receiving data from sensors in the patient's monitoring device in a day. Format: Integer. Possible values: integer numbers between 0 and 24. Example values: 0,1,12,24"
      },
      {
        "ColumnName": "MONITORING_REC.SENSORS_REC.SENSORS_ACTIVE_AVG",
        "DataType": "FLOAT",
        "Description": "Average number of sensors active per hour in the patient's monitoring device in the day specified in the field RECORD_DATE. Format: Float. Example values: 1.875, 2.79, 1.66"
      },
      {
        "ColumnName": "MONITORING_REC.SENSORS_REC.SENSORS_TOTAL_NUM",
        "DataType": "BIGINT",
        "Description": "Total number of distinct sensors in the patient's monitoring device in the day specified in the field RECORD_DATE. Format: Bigint. Example values: 0,1,4,13"
      },
      {
        "ColumnName": "MONITORING_REC.CONTINUOUS_REC.SENSORS_ACTIVE_AVG",
        "DataType": "FLOAT",
        "Description": "Average number of continuous monitoring sensors active per hour in the day specified in the field RECORD_DATE. Format: Float. Example values: 1.875, 2.79, 1.66"
      },
      {
        "ColumnName": "MONITORING_REC.CONTINUOUS_REC.SENSORS_TOTAL_NUM",
        "DataType": "BIGINT",
        "Description": "Total number of distinct continuous monitoring sensors in the day specified in the field RECORD_DATE. Format: Bigint. Example values: 0,1,4,13"
      },
      {
        "ColumnName": "MONITORING_REC.WEARABLE_REC.ALL_TYPES_REC.SENSORS_ACTIVE_AVG",
        "DataType": "FLOAT",
        "Description": "Average number of wearable device sensors active per hour in the day specified in the field RECORD_DATE. Format: Float. Example values: 1.875, 2.79, 1.66"
      },
      {
        "ColumnName": "MONITORING_REC.WEARABLE_REC.ALL_TYPES_REC.SENSORS_TOTAL_NUM",
        "DataType": "BIGINT",
        "Description": "Total number of distinct wearable device sensors in the day specified in the field RECORD_DATE. Format: Bigint. Example values: 0,1,4,13"
      },
      {
        "ColumnName": "MONITORING_REC.WEARABLE_REC.VITAL_SIGNS_REC.SENSORS_ACTIVE_AVG",
        "DataType": "FLOAT",
        "Description": "Average number of vital sign monitoring sensors active per hour in the day specified in the field RECORD_DATE. Format: Float. Example values: 1.875, 2.79, 1.66"
      },
      {
        "ColumnName": "MONITORING_REC.WEARABLE_REC.VITAL_SIGNS_REC.SENSORS_TOTAL_NUM",
        "DataType": "BIGINT",
        "Description": "Total number of distinct vital sign monitoring sensors in the day specified in the field RECORD_DATE. Format: Bigint. Example values: 0,1,4,13"
      },
      {
        "ColumnName": "MONITORING_REC.WEARABLE_REC.ACTIVITY_REC.SENSORS_ACTIVE_AVG",
        "DataType": "FLOAT",
        "Description": "Average number of activity monitoring sensors active per hour in the day specified in the field RECORD_DATE. Format: Float. Example values: 1.875, 2.79, 1.66"
      },
      {
        "ColumnName": "MONITORING_REC.WEARABLE_REC.ACTIVITY_REC.SENSORS_TOTAL_NUM",
        "DataType": "BIGINT",
        "Description": "Total number of distinct activity monitoring sensors in the day specified in the field RECORD_DATE. Format: Bigint. Example values: 0,1,4,13"
      },
      {
        "ColumnName": "HEALTH_REC.HEART_RATE_AVG",
        "DataType": "FLOAT",
        "Description": "Average heart rate recorded for the patient using all devices in the day specified in the field RECORD_DATE. Format: Float. Example values: 68.5, 72.3, 80.1"
      },
      {
        "ColumnName": "HEALTH_REC.HEART_RATE_VITAL_AVG",
        "DataType": "FLOAT",
        "Description": "Average heart rate calculated for the patient using only vital sign monitoring devices in the day specified in the field RECORD_DATE. Format: Float. Example values: 68.5, 72.3, 80.1"
      },
      {
        "ColumnName": "HEALTH_REC.HEART_RATE_ACTIVITY_AVG",
        "DataType": "FLOAT",
        "Description": "Average heart rate calculated for the patient using only activity monitoring devices in the day specified in the field RECORD_DATE. Format: Float. Example values: 72.4, 84.9, 96.2"
      },
      {
        "ColumnName": "HEALTH_REC.WELLNESS_INDEX",
        "DataType": "FLOAT",
        "Description": "Daily Wellness Index for the patient in the day specified in the field RECORD_DATE. Format: Float. Possible values: float numbers between 0 and 100. Example values: 92.7, 84.5"
      },
      {
        "ColumnName": "HEALTH_REC.VITAL_SIGNS_INDEX",
        "DataType": "FLOAT",
        "Description": "Daily Vital Signs Index for the patient in the day specified in the field RECORD_DATE. Format: Float. Possible values: float numbers between 0 and 100. Example values: 95.2, 88.7"
      },
      {
        "ColumnName": "HEALTH_REC.ACTIVITY_INDEX",
        "DataType": "FLOAT",
        "Description": "Daily Activity Index for the patient in the day specified in the field RECORD_DATE. Format: Float. Possible values: float numbers between 0 and 100. Example values: 87.3, 76.5"
      },
      {
        "ColumnName": "HEALTH_REC.OVERALL_HEALTH_INDEX",
        "DataType": "FLOAT",
        "Description": "Daily Health Index for the patient, calculated using all monitoring data. Format: Float. Possible values: float numbers between 0 and 100. Example values: 90.4, 82.6"
      },
      {
        "ColumnName": "HEALTH_REC.ELEVATED_RISK_PERCENTAGE",
        "DataType": "FLOAT",
        "Description": "Percent of sensors indicating elevated risk levels for the patient in the day specified in the field RECORD_DATE. Format: String. Example values: '0', '0.25', '0.68', '0.5'"
      }
    ],
    "Relationships": [
      {
        "ForeignKey": "INSURANCE_REC.ZIP_CODE",
        "ReferencedTable": "D_HC_Geography_v3",
        "ReferencedColumn": "ZIP_CODE"
      },
      {
        "ForeignKey": "INSURANCE_REC.PATIENT_TYPE_ID",
        "ReferencedTable": "D_Patient_Type_v3",
        "ReferencedColumn": "PATIENT_TYPE_ID"
      },
      {
        "ForeignKey": "INSURANCE_REC.INSURANCE_PLAN_ID",
        "ReferencedTable": "D_Insurance_Plan_v3",
        "ReferencedColumn": "PLAN_ID"
      }
    ]
  },
  {
    "TableName": "HC_Patient_Device_Details_v3",
    "Description": "Entity that collects the information associated with the medical devices used by patients on a daily basis.",
    "Columns": [
      {
        "ColumnName": "RECORD_DATE",
        "DataType": "VARCHAR",
        "Description": "Year, month and day of the data. Format: YYYY-MM-DD (4 digits for year, months from 01 to 12, days from 01 to 31). Example values: '2023-04-24', '2024-09-16', '2022-06-01'"
      },
      {
        "ColumnName": "PATIENT_ID",
        "DataType": "VARCHAR",
        "Description": "Unique Identifier of the patient within the healthcare system. Format: String. Example values: '164559592362680187', '-6149090817956898776'"
      },
      {
        "ColumnName": "PROVIDER_ID",
        "DataType": "VARCHAR",
        "Description": "Identifier of the healthcare provider. Format: String. Example values: '0401', '0403'"
      },
      {
        "ColumnName": "USER_PORTAL_ID",
        "DataType": "VARCHAR",
        "Description": "Unique identifier of the user in the Patient Portal platform. Format: String. Example values: '3706277557884218994', '-6189348075566519429'"
      },
      {
        "ColumnName": "PHONE_NUMBER",
        "DataType": "VARCHAR",
        "Description": "Phone number of the patient, with international prefix. Format: Phone number in ITU E.164 format. Example values: '+14155552671', '+442071838750'"
      },
      {
        "ColumnName": "DEVICE_ID",
        "DataType": "VARCHAR",
        "Description": "Unique identifier of the medical device used by the patient. Format: String. Example values: '8118065208874483378', '-5152502139752491594'"
      },
      {
        "ColumnName": "DEVICE_OS",
        "DataType": "VARCHAR",
        "Description": "Device operating system. If unknown, the value will be null. Format: String. Example values: 'Embedded Linux 4.0', 'Android 13', 'iOS 15', null"
      },
      {
        "ColumnName": "DEVICE_OS_TYPE",
        "DataType": "VARCHAR",
        "Description": "Device kernel operating system. If unknown, the value will be null. Format: String. Exact enumerated values: 'Linux', 'Android', 'iOS', 'Proprietary', null"
      },
      {
        "ColumnName": "DEVICE_BRAND",
        "DataType": "VARCHAR",
        "Description": "Commercial brand of the medical device. If unknown, the value will be null. Format: String. Example values: 'Medtronic', 'Abbott', 'Philips', 'Dexcom'"
      },
      {
        "ColumnName": "DEVICE_MODEL",
        "DataType": "VARCHAR",
        "Description": "Model of the medical device. If unknown, the value will be null. Format: String. Example values: 'Guardian 4', 'Libre 3', 'HealthMonitor X1'"
      },
      {
        "ColumnName": "DEVICE_TYPE",
        "DataType": "VARCHAR",
        "Description": "Type of medical device. Format: String. Exact enumerated values: 'CGM', 'Insulin Pump', 'Blood Pressure Monitor', 'ECG Monitor', 'Pulse Oximeter', 'Activity Tracker', 'Smart Scale'"
      },
      {
        "ColumnName": "DEVICE_CATEGORY",
        "DataType": "VARCHAR",
        "Description": "Category of the device. Format: String. Exact enumerated values: 'Wearable', 'Implanted', 'Portable', 'Stationary', 'Remote'"
      },
      {
        "ColumnName": "DEVICE_CONNECTIVITY",
        "DataType": "VARCHAR",
        "Description": "Primary connectivity method of the device. Format: String. Exact enumerated values: 'Bluetooth', 'WiFi', 'Cellular', 'NFC', 'Proprietary'"
      },
      {
        "ColumnName": "DEVICE_BATTERY_POWERED",
        "DataType": "BOOLEAN",
        "Description": "Boolean value that is true when the device is battery powered. Format: Boolean. Possible values: true or false."
      },
      {
        "ColumnName": "DEVICE_RECHARGEABLE",
        "DataType": "BOOLEAN",
        "Description": "Boolean value that is true when the device has a rechargeable battery. Format: Boolean. Possible values: true or false."
      },
      {
        "ColumnName": "DEVICE_FDA_APPROVED",
        "DataType": "BOOLEAN",
        "Description": "Boolean value that is true when the device is FDA approved. Format: Boolean. Possible values: true or false."
      },
      {
        "ColumnName": "DEVICE_MEDICAL_GRADE",
        "DataType": "VARCHAR",
        "Description": "Medical grade classification of the device. Format: String. Exact enumerated values: 'Class I', 'Class II', 'Class III', 'Consumer', 'Investigational'"
      },
      {
        "ColumnName": "CONDITION_MONITORED",
        "DataType": "VARCHAR",
        "Description": "Primary medical condition being monitored. Format: String. Example values: 'Diabetes', 'Hypertension', 'Cardiac Arrhythmia', 'Sleep Apnea'"
      },
      {
        "ColumnName": "DEVICE_PRESCRIPTION_REQUIRED",
        "DataType": "BOOLEAN",
        "Description": "Boolean value that is true when the device requires a prescription. Format: Boolean. Possible values: true or false."
      },
      {
        "ColumnName": "DEVICE_INSURANCE_COVERED",
        "DataType": "BOOLEAN",
        "Description": "Boolean value that is true when the device is covered by insurance. Format: Boolean. Possible values: true or false."
      },
      {
        "ColumnName": "DEVICE_ACTIVE_HOURS",
        "DataType": "FLOAT",
        "Description": "Number of hours the device was active on the recorded date. Format: Float. Example values: 12.5, 24.0, 8.25"
      },
      {
        "ColumnName": "DEVICE_READINGS_NUM",
        "DataType": "INT",
        "Description": "Number of readings recorded by the device on the record date. Format: Integer. Example values: 24, 288, 1440"
      },
      {
        "ColumnName": "DEVICE_ACCURACY_PERCENT",
        "DataType": "FLOAT",
        "Description": "Calculated accuracy percentage of the device readings. Format: Float. Example values: 98.5, 92.3, 99.1"
      },
      {
        "ColumnName": "DEVICE_MAINTENANCE_DUE_DAYS",
        "DataType": "INT",
        "Description": "Number of days until maintenance is due for the device. Format: Integer. Example values: 30, 90, 365"
      },
      {
        "ColumnName": "DEVICE_CALIBRATION_DUE_DAYS",
        "DataType": "INT",
        "Description": "Number of days until calibration is due for the device. Format: Integer. Example values: 7, 14, 30"
      },
      {
        "ColumnName": "DEVICE_TYPE_CATEGORY",
        "DataType": "VARCHAR",
        "Description": "Higher level device type grouping. Exact enumerated values: 'Glucose Monitoring', 'Cardiovascular', 'Respiratory', 'Physical Activity', 'Sleep', 'Weight Management', 'Medication Management'"
      },
      {
        "ColumnName": "DEVICE_ENERGY_EFFICIENCY",
        "DataType": "BOOLEAN",
        "Description": "Indicates if the device has energy efficiency features. Format: Boolean. Possible values: true or false."
      },
      {
        "ColumnName": "EXTRACTION_TIME",
        "DataType": "VARCHAR",
        "Description": "Date-time of the record extraction. Format: YYYY-MM-DD HH:MM:SS."
      }
    ],
    "Relationships": [
        {
            "ForeignKey": "PATIENT_ID",
            "ReferencedTable": "HC_Patient_Daily_Summary_v3",
            "ReferencedColumn": "PATIENT_ID"
        },
        {
            "ForeignKey": "PROVIDER_ID",
            "ReferencedTable": "D_HC_Providers_v3",
            "ReferencedColumn": "PROVIDER_ID"
        }
        ]
    },
  {
    "TableName": "HC_Patient_Medication_Summary_v3",
    "Description": "Entity that collects the information associated with patient medication usage and adherence on a daily basis.",
    "Columns": [
      {
        "ColumnName": "RECORD_DATE",
        "DataType": "VARCHAR",
        "Description": "Year, month and day of the data. Format: YYYY-MM-DD. Example values: '2023-04-24', '2024-09-16', '2022-06-01'"
      },
      {
        "ColumnName": "PATIENT_ID",
        "DataType": "VARCHAR",
        "Description": "Unique Identifier of the patient. Format: String. Example values: '164559592362680187', '-6149090817956898776'"
      },
      {
        "ColumnName": "PROVIDER_ID",
        "DataType": "VARCHAR",
        "Description": "Identifier of the healthcare provider. Format: String. Example values: '0401', '0403'"
      },
      {
        "ColumnName": "MEDICATION_ID",
        "DataType": "VARCHAR",
        "Description": "Unique identifier of the medication. Format: String. Example values: '812807654', '945322178'"
      },
      {
        "ColumnName": "PRESCRIPTION_ID",
        "DataType": "VARCHAR",
        "Description": "Unique identifier of the prescription. Format: String. Example values: '7123456789', '8234567890'"
      },
      {
        "ColumnName": "MEDICATION_NAME",
        "DataType": "VARCHAR",
        "Description": "Name of the medication. Format: String. Example values: 'Metformin', 'Lisinopril', 'Atorvastatin'"
      },
      {
        "ColumnName": "MEDICATION_GENERIC_NAME",
        "DataType": "VARCHAR",
        "Description": "Generic name of the medication. Format: String. Example values: 'Metformin', 'Lisinopril', 'Atorvastatin'"
      },
      {
        "ColumnName": "MEDICATION_STRENGTH",
        "DataType": "VARCHAR",
        "Description": "Strength of the medication. Format: String. Example values: '500mg', '10mg', '20mg'"
      },
      {
        "ColumnName": "MEDICATION_FORM",
        "DataType": "VARCHAR",
        "Description": "Form of the medication. Format: String. Exact enumerated values: 'Tablet', 'Capsule', 'Liquid', 'Injection', 'Patch', 'Inhaler', 'Suppository'"
      },
      {
        "ColumnName": "MEDICATION_FREQUENCY",
        "DataType": "VARCHAR",
        "Description": "Frequency of medication administration. Format: String. Example values: 'Once daily', 'Twice daily', 'Every 8 hours', 'As needed'"
      },
      {
        "ColumnName": "MEDICATION_ROUTE",
        "DataType": "VARCHAR",
        "Description": "Route of medication administration. Format: String. Exact enumerated values: 'Oral', 'Intravenous', 'Intramuscular', 'Subcutaneous', 'Topical', 'Inhalation', 'Rectal'"
      },
      {
        "ColumnName": "MEDICATION_CLASS",
        "DataType": "VARCHAR",
        "Description": "Therapeutic class of the medication. Format: String. Example values: 'Antidiabetic', 'Antihypertensive', 'Statin', 'NSAID', 'Antibiotic'"
      },
      {
        "ColumnName": "MEDICATION_CONDITION",
        "DataType": "VARCHAR",
        "Description": "Medical condition being treated. Format: String. Example values: 'Diabetes', 'Hypertension', 'Hyperlipidemia', 'Depression'"
      },
      {
        "ColumnName": "MEDICATION_START_DATE",
        "DataType": "VARCHAR",
        "Description": "Date medication was started. Format: YYYY-MM-DD. Example values: '2022-01-15', '2023-06-22'"
      },
      {
        "ColumnName": "MEDICATION_END_DATE",
        "DataType": "VARCHAR",
        "Description": "Date medication is scheduled to end, if applicable. Format: YYYY-MM-DD. Example values: '2022-02-15', '2023-12-31', null"
      },
      {
        "ColumnName": "MEDICATION_PRESCRIBED_BY",
        "DataType": "VARCHAR",
        "Description": "ID of the provider who prescribed the medication. Format: String. Example values: '123456', '789012'"
      },
      {
        "ColumnName": "MEDICATION_PRESCRIBED_DATE",
        "DataType": "VARCHAR",
        "Description": "Date medication was prescribed. Format: YYYY-MM-DD. Example values: '2022-01-10', '2023-06-20'"
      },
      {
        "ColumnName": "DOSES_PRESCRIBED",
        "DataType": "INT",
        "Description": "Number of doses prescribed. Format: Integer. Example values: 30, 60, 90"
      },
      {
        "ColumnName": "DOSES_DISPENSED",
        "DataType": "INT",
        "Description": "Number of doses dispensed. Format: Integer. Example values: 30, 60, 90"
      },
      {
        "ColumnName": "REFILLS_AUTHORIZED",
        "DataType": "INT",
        "Description": "Number of refills authorized. Format: Integer. Example values: 0, 1, 3, 11"
      },
      {
        "ColumnName": "REFILLS_REMAINING",
        "DataType": "INT",
        "Description": "Number of refills remaining. Format: Integer. Example values: 0, 1, 3, 11"
      },
      {
        "ColumnName": "ADHERENCE_RATE",
        "DataType": "FLOAT",
        "Description": "Medication adherence rate for the record date. Format: Float between 0 and 1. Example values: 0.8, 1.0, 0.5"
      },
      {
        "ColumnName": "ADHERENCE_LEVEL",
        "DataType": "VARCHAR",
        "Description": "Categorization of adherence level. Format: String. Exact enumerated values: 'High', 'Medium', 'Low', 'None'"
      },
      {
        "ColumnName": "DOSES_TAKEN_TODAY",
        "DataType": "INT",
        "Description": "Number of doses taken on the record date. Format: Integer. Example values: 0, 1, 2, 3"
      },
      {
        "ColumnName": "DOSES_MISSED_TODAY",
        "DataType": "INT",
        "Description": "Number of doses missed on the record date. Format: Integer. Example values: 0, 1, 2"
      },
      {
        "ColumnName": "MEDICATION_INSURANCE_COVERED",
        "DataType": "BOOLEAN",
        "Description": "Boolean value that is true when the medication is covered by insurance. Format: Boolean. Possible values: true or false."
      },
      {
        "ColumnName": "MEDICATION_TIER",
        "DataType": "VARCHAR",
        "Description": "Insurance formulary tier of the medication. Format: String. Example values: 'Tier 1', 'Tier 2', 'Tier 3', 'Specialty'"
      },
      {
        "ColumnName": "PATIENT_COST",
        "DataType": "FLOAT",
        "Description": "Patient's out-of-pocket cost for the medication. Format: Float. Example values: 0.00, 10.50, 124.99"
      },
      {
        "ColumnName": "INSURANCE_COST",
        "DataType": "FLOAT",
        "Description": "Insurance's cost for the medication. Format: Float. Example values: 15.00, 87.50, 345.75"
      },
      {
        "ColumnName": "SIDE_EFFECTS_REPORTED",
        "DataType": "BOOLEAN",
        "Description": "Boolean value that is true when side effects were reported for the record date. Format: Boolean. Possible values: true or false."
      },
      {
        "ColumnName": "EXTRACTION_TIME",
        "DataType": "VARCHAR",
        "Description": "Date-time of the record extraction. Format: YYYY-MM-DD HH:MM:SS."
      }
    ],
    "Relationships": [
        {
            "ForeignKey": "PATIENT_ID",
            "ReferencedTable": "HC_Patient_Daily_Summary_v3",
            "ReferencedColumn": "PATIENT_ID"
        },
        {
            "ForeignKey": "PROVIDER_ID",
            "ReferencedTable": "D_HC_Providers_v3",
            "ReferencedColumn": "PROVIDER_ID"
        },
        {
            "ForeignKey": "MEDICATION_PRESCRIBED_BY",
            "ReferencedTable": "D_HC_Providers_v3",
            "ReferencedColumn": "PROVIDER_ID"
        }
    ]
  },
  {
    "TableName": "D_Patient_Type_v3",
    "Description": "Classifications of the patients, attending to different typing criteria, for care management and administrative purposes",
    "Columns": [
      {
        "ColumnName": "SYSTEM_ID",
        "DataType": "VARCHAR",
        "Description": "Global System Identifier (System acting as owner of the information present in the current entity)"
      },
      {
        "ColumnName": "PATIENT_TYPE_ID",
        "DataType": "VARCHAR",
        "Description": "Organizational patient type classification. FORMAT: Two-letter code."
      },
      {
        "ColumnName": "PATIENT_TYPE_DESCRIPTION",
        "DataType": "VARCHAR",
        "Description": "Patient type description. This is the actual name of the patient type. POSSIBLE VALUES: 'Inpatient', 'Outpatient', 'Emergency', 'Ambulatory', 'Intensive Care', 'Long-term Care', 'Specialty Care', 'Primary Care', 'Children', 'Other'"
      },
      {
        "ColumnName": "GLOBAL_PATIENT_TYPE_ID",
        "DataType": "VARCHAR",
        "Description": "ID of the global patient type classification"
      },
      {
        "ColumnName": "PATIENT_GROUP_ID",
        "DataType": "VARCHAR",
        "Description": "ID code of the patient grouping"
      },
      {
        "ColumnName": "PATIENT_GROUP_DESCRIPTION",
        "DataType": "VARCHAR",
        "Description": "Description of the patient grouping"
      },
      {
        "ColumnName": "LOS_MIN_DAYS",
        "DataType": "INT",
        "Description": "Minimum length of stay in days for this patient type"
      },
      {
        "ColumnName": "LOS_MAX_DAYS",
        "DataType": "INT",
        "Description": "Maximum typical length of stay in days for this patient type"
      },
      {
        "ColumnName": "REQUIRES_ADMISSION",
        "DataType": "BOOLEAN",
        "Description": "Whether this patient type requires formal admission to the facility"
      },
      {
        "ColumnName": "BED_REQUIRED",
        "DataType": "BOOLEAN",
        "Description": "Whether this patient type requires an assigned bed"
      },
      {
        "ColumnName": "EXTRACTION_TIME",
        "DataType": "VARCHAR",
        "Description": "Date-time of the record extraction"
      }
    ]
  },
  {
    "TableName": "D_Insurance_Plan_v3",
    "Description": "Every health insurance plan available to patients, including coverage details, network information, and benefits",
    "Columns": [
      {
        "ColumnName": "SYSTEM_ID",
        "DataType": "VARCHAR",
        "Description": "Global System Identifier (System acting as owner of the information present in the current entity)"
      },
      {
        "ColumnName": "EFFECTIVE_DATE",
        "DataType": "VARCHAR",
        "Description": "Year, month and day from which the plan information is effective. Format: YYYY-MM-DD."
      },
      {
        "ColumnName": "PLAN_ID",
        "DataType": "VARCHAR",
        "Description": "Unique identifier of the insurance plan"
      },
      {
        "ColumnName": "PLAN_NAME",
        "DataType": "VARCHAR",
        "Description": "Name/short description of the insurance plan"
      },
      {
        "ColumnName": "PRIMARY_CARE_COVERED",
        "DataType": "BOOLEAN",
        "Description": "Indicates whether the plan covers primary care visits. Values: 0=No; 1=Yes."
      },
      {
        "ColumnName": "SPECIALIST_CARE_COVERED",
        "DataType": "BOOLEAN",
        "Description": "Indicates whether the plan covers specialist care visits. Values: 0=No; 1=Yes."
      },
      {
        "ColumnName": "EMERGENCY_CARE_COVERED",
        "DataType": "BOOLEAN",
        "Description": "Indicates whether the plan covers emergency care. Values: 0=No; 1=Yes."
      },
      {
        "ColumnName": "HOSPITAL_CARE_COVERED",
        "DataType": "BOOLEAN",
        "Description": "Indicates whether the plan covers hospital care. Values: 0=No; 1=Yes."
      },
      {
        "ColumnName": "PREVENTIVE_CARE_COVERED",
        "DataType": "BOOLEAN",
        "Description": "Indicates whether the plan covers preventive care. Values: 0=No; 1=Yes."
      },
      {
        "ColumnName": "PRESCRIPTION_DRUGS_COVERED",
        "DataType": "BOOLEAN",
        "Description": "Indicates whether the plan covers prescription drugs. Values: 0=No; 1=Yes."
      },
      {
        "ColumnName": "MENTAL_HEALTH_COVERED",
        "DataType": "BOOLEAN",
        "Description": "Indicates whether the plan covers mental health services. Values: 0=No; 1=Yes."
      },
      {
        "ColumnName": "DENTAL_COVERED",
        "DataType": "BOOLEAN",
        "Description": "Indicates whether the plan covers dental services. Values: 0=No; 1=Yes."
      },
      {
        "ColumnName": "VISION_COVERED",
        "DataType": "BOOLEAN",
        "Description": "Indicates whether the plan covers vision services. Values: 0=No; 1=Yes."
      },
      {
        "ColumnName": "TELEHEALTH_COVERED",
        "DataType": "BOOLEAN",
        "Description": "Indicates whether the plan covers telehealth services. Values: 0=No; 1=Yes."
      },
      {
        "ColumnName": "ANNUAL_DEDUCTIBLE_INDIVIDUAL",
        "DataType": "FLOAT",
        "Description": "Annual deductible amount for individual coverage"
      },
      {
        "ColumnName": "ANNUAL_DEDUCTIBLE_FAMILY",
        "DataType": "FLOAT",
        "Description": "Annual deductible amount for family coverage"
      },
      {
        "ColumnName": "OUT_OF_POCKET_MAX_INDIVIDUAL",
        "DataType": "FLOAT",
        "Description": "Out-of-pocket maximum amount for individual coverage"
      },
      {
        "ColumnName": "OUT_OF_POCKET_MAX_FAMILY",
        "DataType": "FLOAT",
        "Description": "Out-of-pocket maximum amount for family coverage"
      },
      {
        "ColumnName": "PRIMARY_CARE_COPAY",
        "DataType": "FLOAT",
        "Description": "Copay amount for primary care visits"
      },
      {
        "ColumnName": "SPECIALIST_CARE_COPAY",
        "DataType": "FLOAT",
        "Description": "Copay amount for specialist care visits"
      },
      {
        "ColumnName": "EMERGENCY_CARE_COPAY",
        "DataType": "FLOAT",
        "Description": "Copay amount for emergency care"
      },
      {
        "ColumnName": "PLAN_TYPE",
        "DataType": "VARCHAR",
        "Description": "Type of insurance plan. Format: String. Exact enumerated values: 'HMO', 'PPO', 'EPO', 'POS', 'HDHP', 'Medicare', 'Medicaid', 'Medicare Advantage'"
      },
      {
        "ColumnName": "NETWORK_SIZE",
        "DataType": "VARCHAR",
        "Description": "Description of the plan's provider network size. Format: String. Exact enumerated values: 'Limited', 'Moderate', 'Extensive', 'Open'"
      },
      {
        "ColumnName": "METAL_LEVEL",
        "DataType": "VARCHAR",
        "Description": "ACA metal level of the plan. Format: String. Exact enumerated values: 'Bronze', 'Silver', 'Gold', 'Platinum', 'Catastrophic', 'Not Applicable'"
      },
      {
        "ColumnName": "PLAN_START_DATE",
        "DataType": "VARCHAR",
        "Description": "Start date of the insurance plan validity. Format: YYYY-MM-DD."
      },
      {
        "ColumnName": "PLAN_END_DATE",
        "DataType": "VARCHAR",
        "Description": "End date of the insurance plan validity. Format: YYYY-MM-DD."
      },
      {
        "ColumnName": "INSURER_ID",
        "DataType": "VARCHAR",
        "Description": "Identifier of the insurance company offering the plan"
      },
      {
        "ColumnName": "INSURANCE_GROUP",
        "DataType": "VARCHAR",
        "Description": "Category of insurance. Format: String. Exact enumerated values: 'Individual', 'Small Group', 'Large Group', 'Government', 'Self-Insured'"
      },
      {
        "ColumnName": "MARKETPLACE_PLAN",
        "DataType": "BOOLEAN",
        "Description": "Indicates if the plan is available on the ACA marketplace. Values: 0=No; 1=Yes."
      },
      {
        "ColumnName": "EXTRACTION_TIME",
        "DataType": "VARCHAR",
        "Description": "Date-time of the record extraction"
      }
    ],
    "Relationships": [
        {
            "ForeignKey": "INSURER_ID",
            "ReferencedTable": "D_HC_Insurers_v3",
            "ReferencedColumn": "INSURER_ID"
        }
    ]
  },
  {
    "TableName": "D_HC_Geography_v3",
    "Description": "Geographical information for healthcare service areas, including demographic and healthcare accessibility data",
    "Columns": [
      {
        "ColumnName": "SYSTEM_ID",
        "DataType": "VARCHAR",
        "Description": "Global System Identifier (System acting as owner of the information present in the current entity)"
      },
      {
        "ColumnName": "ZIP_CODE",
        "DataType": "VARCHAR",
        "Description": "ZIP code identifier"
      },
      {
        "ColumnName": "CITY",
        "DataType": "VARCHAR",
        "Description": "City name"
      },
      {
        "ColumnName": "COUNTY",
        "DataType": "VARCHAR",
        "Description": "County name"
      },
      {
        "ColumnName": "STATE",
        "DataType": "VARCHAR",
        "Description": "State name or abbreviation"
      },
      {
        "ColumnName": "COUNTRY",
        "DataType": "VARCHAR",
        "Description": "Country name"
      },
      {
        "ColumnName": "LATITUDE",
        "DataType": "FLOAT",
        "Description": "Latitude coordinate of the geographic center of the ZIP code"
      },
      {
        "ColumnName": "LONGITUDE",
        "DataType": "FLOAT",
        "Description": "Longitude coordinate of the geographic center of the ZIP code"
      },
      {
        "ColumnName": "POPULATION",
        "DataType": "INT",
        "Description": "Estimated population within the ZIP code"
      },
      {
        "ColumnName": "MEDIAN_AGE",
        "DataType": "FLOAT",
        "Description": "Median age of residents in the ZIP code"
      },
      {
        "ColumnName": "MEDIAN_HOUSEHOLD_INCOME",
        "DataType": "FLOAT",
        "Description": "Median household income in the ZIP code"
      },
      {
        "ColumnName": "AREA_TYPE",
        "DataType": "VARCHAR",
        "Description": "Classification of area type. Format: String. Exact enumerated values: 'Urban', 'Suburban', 'Rural', 'Remote'"
      },
      {
        "ColumnName": "HEALTHCARE_FACILITIES_COUNT",
        "DataType": "INT",
        "Description": "Number of healthcare facilities in the ZIP code"
      },
      {
        "ColumnName": "PRIMARY_CARE_PHYSICIANS_COUNT",
        "DataType": "INT",
        "Description": "Number of primary care physicians in the ZIP code"
      },
      {
        "ColumnName": "SPECIALISTS_COUNT",
        "DataType": "INT",
        "Description": "Number of specialist physicians in the ZIP code"
      },
      {
        "ColumnName": "HOSPITAL_BEDS_COUNT",
        "DataType": "INT",
        "Description": "Number of hospital beds in the ZIP code"
      },
      {
        "ColumnName": "ICU_BEDS_COUNT",
        "DataType": "INT",
        "Description": "Number of ICU beds in the ZIP code"
      },
      {
        "ColumnName": "HEALTHCARE_ACCESS_INDEX",
        "DataType": "FLOAT",
        "Description": "Calculated index of healthcare accessibility in the area (0-100)"
      },
      {
        "ColumnName": "AVERAGE_TRAVEL_TIME_TO_HOSPITAL",
        "DataType": "FLOAT",
        "Description": "Average travel time to nearest hospital in minutes"
      },
      {
        "ColumnName": "UNINSURED_RATE",
        "DataType": "FLOAT",
        "Description": "Percentage of population without health insurance"
      },
      {
        "ColumnName": "HEALTH_PROFESSIONAL_SHORTAGE_AREA",
        "DataType": "BOOLEAN",
        "Description": "Indicates if the area is designated as a Health Professional Shortage Area"
      },
      {
        "ColumnName": "MEDICALLY_UNDERSERVED_AREA",
        "DataType": "BOOLEAN",
        "Description": "Indicates if the area is designated as a Medically Underserved Area"
      },
      {
        "ColumnName": "BROADBAND_ACCESS_RATE",
        "DataType": "FLOAT",
        "Description": "Percentage of population with broadband internet access"
      },
      {
        "ColumnName": "TELEHEALTH_UTILIZATION_RATE",
        "DataType": "FLOAT",
        "Description": "Rate of telehealth utilization in the area"
      },
      {
        "ColumnName": "EXTRACTION_TIME",
        "DataType": "VARCHAR",
        "Description": "Date-time of the record extraction"
      }
    ]
  },
  {
    "TableName": "D_HC_Procedures_v3",
    "Description": "Catalog of medical procedures, including CPT codes, descriptions, complexity levels, and associated specialties",
    "Columns": [
      {
        "ColumnName": "SYSTEM_ID",
        "DataType": "VARCHAR",
        "Description": "Global System Identifier (System acting as owner of the information present in the current entity)"
      },
      {
        "ColumnName": "PROCEDURE_CODE",
        "DataType": "VARCHAR",
        "Description": "Unique identifier for the procedure (CPT or HCPCS code)"
      },
      {
        "ColumnName": "PROCEDURE_DESCRIPTION",
        "DataType": "VARCHAR",
        "Description": "Full description of the medical procedure"
      },
      {
        "ColumnName": "PROCEDURE_SHORT_DESCRIPTION",
        "DataType": "VARCHAR",
        "Description": "Short description of the medical procedure"
      },
      {
        "ColumnName": "PROCEDURE_CATEGORY",
        "DataType": "VARCHAR",
        "Description": "Category of the procedure. Format: String. Example values: 'Evaluation and Management', 'Surgery', 'Radiology', 'Laboratory', 'Medicine'"
      },
      {
        "ColumnName": "PROCEDURE_SUBCATEGORY",
        "DataType": "VARCHAR",
        "Description": "Subcategory of the procedure. Format: String. Example values: 'Office Visit', 'CT Scan', 'Blood Test', 'Surgical Procedure'"
      },
      {
        "ColumnName": "PRIMARY_SPECIALTY",
        "DataType": "VARCHAR",
        "Description": "Primary medical specialty associated with the procedure"
      },
      {
        "ColumnName": "SECONDARY_SPECIALTIES",
        "DataType": "VARCHAR",
        "Description": "Secondary medical specialties that may perform the procedure, comma-separated"
      },
      {
        "ColumnName": "COMPLEXITY_LEVEL",
        "DataType": "VARCHAR",
        "Description": "Level of complexity of the procedure. Format: String. Exact enumerated values: 'Low', 'Moderate', 'High', 'Very High'"
      },
      {
        "ColumnName": "RISK_LEVEL",
        "DataType": "VARCHAR",
        "Description": "Level of risk associated with the procedure. Format: String. Exact enumerated values: 'Minimal', 'Low', 'Moderate', 'High'"
      },
      {
        "ColumnName": "TYPICAL_DURATION_MINUTES",
        "DataType": "INT",
        "Description": "Typical duration of the procedure in minutes"
      },
      {
        "ColumnName": "PRE_PROCEDURE_PREPARATION",
        "DataType": "VARCHAR",
        "Description": "Description of required pre-procedure preparation"
      },
      {
        "ColumnName": "POST_PROCEDURE_CARE",
        "DataType": "VARCHAR",
        "Description": "Description of required post-procedure care"
      },
      {
        "ColumnName": "ANESTHESIA_REQUIRED",
        "DataType": "BOOLEAN",
        "Description": "Indicates if anesthesia is typically required for the procedure"
      },
      {
        "ColumnName": "ANESTHESIA_TYPE",
        "DataType": "VARCHAR",
        "Description": "Type of anesthesia typically used. Format: String. Exact enumerated values: 'Local', 'Regional', 'Conscious Sedation', 'General', 'None'"
      },
      {
        "ColumnName": "INPATIENT_REQUIRED",
        "DataType": "BOOLEAN",
        "Description": "Indicates if the procedure typically requires inpatient admission"
      },
      {
        "ColumnName": "AVERAGE_COST",
        "DataType": "FLOAT",
        "Description": "Average cost of the procedure in USD"
      },
      {
        "ColumnName": "MEDICARE_PAYMENT_RATE",
        "DataType": "FLOAT",
        "Description": "Medicare payment rate for the procedure in USD"
      },
      {
        "ColumnName": "FACILITY_SETTING",
        "DataType": "VARCHAR",
        "Description": "Typical setting where procedure is performed. Format: String. Exact enumerated values: 'Inpatient Hospital', 'Outpatient Hospital', 'Ambulatory Surgical Center', 'Physician Office', 'Clinic'"
      },
      {
        "ColumnName": "REQUIRES_SPECIAL_EQUIPMENT",
        "DataType": "BOOLEAN",
        "Description": "Indicates if the procedure requires specialized equipment"
      },
      {
        "ColumnName": "REQUIRES_PRIOR_AUTHORIZATION",
        "DataType": "BOOLEAN",
        "Description": "Indicates if the procedure typically requires prior authorization from insurers"
      },
      {
        "ColumnName": "CODE_EFFECTIVE_DATE",
        "DataType": "VARCHAR",
        "Description": "Date when the procedure code became effective. Format: YYYY-MM-DD."
      },
      {
        "ColumnName": "CODE_END_DATE",
        "DataType": "VARCHAR",
        "Description": "Date when the procedure code becomes inactive. Format: YYYY-MM-DD."
      },
      {
        "ColumnName": "EXTRACTION_TIME",
        "DataType": "VARCHAR",
        "Description": "Date-time of the record extraction"
      }
    ]
  },
  {
    "TableName": "D_HC_Providers_v3",
    "Description": "Information about healthcare providers including specialties, locations, and network affiliations",
    "Columns": [
      {
        "ColumnName": "SYSTEM_ID",
        "DataType": "VARCHAR",
        "Description": "Global System Identifier (System acting as owner of the information present in the current entity)"
      },
      {
        "ColumnName": "PROVIDER_ID",
        "DataType": "VARCHAR",
        "Description": "Unique identifier for the healthcare provider"
      },
      {
        "ColumnName": "PROVIDER_TYPE",
        "DataType": "VARCHAR",
        "Description": "Type of provider. Format: String. Exact enumerated values: 'Hospital', 'Clinic', 'Physician Group', 'Urgent Care', 'Laboratory', 'Imaging Center', 'Pharmacy', 'Individual Provider'"
      },
      {
        "ColumnName": "PROVIDER_NAME",
        "DataType": "VARCHAR",
        "Description": "Full name of the provider organization or individual"
      },
      {
        "ColumnName": "PRIMARY_SPECIALTY",
        "DataType": "VARCHAR",
        "Description": "Primary medical specialty of the provider"
      },
      {
        "ColumnName": "SECONDARY_SPECIALTIES",
        "DataType": "VARCHAR",
        "Description": "Secondary medical specialties of the provider, comma-separated"
      },
      {
        "ColumnName": "ADDRESS_LINE_1",
        "DataType": "VARCHAR",
        "Description": "First line of the provider's physical address"
      },
      {
        "ColumnName": "ADDRESS_LINE_2",
        "DataType": "VARCHAR",
        "Description": "Second line of the provider's physical address, if applicable"
      },
      {
        "ColumnName": "CITY",
        "DataType": "VARCHAR",
        "Description": "City of the provider's physical address"
      },
      {
        "ColumnName": "STATE",
        "DataType": "VARCHAR",
        "Description": "State of the provider's physical address"
      },
      {
        "ColumnName": "ZIP_CODE",
        "DataType": "VARCHAR",
        "Description": "ZIP code of the provider's physical address"
      },
      {
        "ColumnName": "PHONE_NUMBER",
        "DataType": "VARCHAR",
        "Description": "Primary contact phone number for the provider"
      },
      {
        "ColumnName": "EMAIL",
        "DataType": "VARCHAR",
        "Description": "Primary contact email address for the provider"
      },
      {
        "ColumnName": "WEBSITE",
        "DataType": "VARCHAR",
        "Description": "Provider's website URL"
      },
      {
        "ColumnName": "NPI_NUMBER",
        "DataType": "VARCHAR",
        "Description": "National Provider Identifier number"
      },
      {
        "ColumnName": "ACCEPTING_NEW_PATIENTS",
        "DataType": "BOOLEAN",
        "Description": "Indicates if the provider is currently accepting new patients"
      },
      {
        "ColumnName": "TELEHEALTH_AVAILABLE",
        "DataType": "BOOLEAN",
        "Description": "Indicates if the provider offers telehealth services"
      },
      {
        "ColumnName": "HOSPITAL_AFFILIATION",
        "DataType": "VARCHAR",
        "Description": "Hospital(s) the provider is affiliated with, comma-separated"
      },
      {
        "ColumnName": "INSURANCE_NETWORKS",
        "DataType": "VARCHAR",
        "Description": "Insurance networks the provider participates in, comma-separated"
      },
      {
        "ColumnName": "LANGUAGES",
        "DataType": "VARCHAR",
        "Description": "Languages spoken by the provider or translation services available, comma-separated"
      },
      {
        "ColumnName": "YEARS_IN_PRACTICE",
        "DataType": "INT",
        "Description": "Number of years the provider has been in practice"
      },
      {
        "ColumnName": "BOARD_CERTIFIED",
        "DataType": "BOOLEAN",
        "Description": "Indicates if the provider is board certified in their specialty"
      },
      {
        "ColumnName": "MEDICAL_SCHOOL",
        "DataType": "VARCHAR",
        "Description": "Medical school attended by the provider"
      },
      {
        "ColumnName": "RESIDENCY",
        "DataType": "VARCHAR",
        "Description": "Residency program completed by the provider"
      },
      {
        "ColumnName": "FELLOWSHIP",
        "DataType": "VARCHAR",
        "Description": "Fellowship program completed by the provider, if applicable"
      },
      {
        "ColumnName": "PROVIDER_GENDER",
        "DataType": "VARCHAR",
        "Description": "Gender of the provider. Format: String. Exact enumerated values: 'Male', 'Female', 'Non-binary', 'Not Specified'"
      },
      {
        "ColumnName": "QUALITY_RATING",
        "DataType": "FLOAT",
        "Description": "Overall quality rating of the provider (0-5 scale)"
      },
      {
        "ColumnName": "EXTRACTION_TIME",
        "DataType": "VARCHAR",
        "Description": "Date-time of the record extraction"
      }
    ],
    "Relationships": [
        {
            "ForeignKey": "ZIP_CODE",
            "ReferencedTable": "D_HC_Geography_v3",
            "ReferencedColumn": "ZIP_CODE"
        }
        ]
  },
  {
    "TableName": "D_Patient_Devices_v3",
    "Description": "Information about patient devices including type, manufacturer, model, and status",
    "Columns": [
      {
        "ColumnName": "PATIENT_ID",
        "DataType": "VARCHAR",
        "Description": "Unique identifier for the patient"
      },
      {
        "ColumnName": "DEVICE_ID",
        "DataType": "VARCHAR",
        "Description": "Unique identifier for the device"
      },
      {
        "ColumnName": "DEVICE_TYPE",
        "DataType": "VARCHAR",
        "Description": "Type of the device"
      },
      {
        "ColumnName": "MANUFACTURER",
        "DataType": "VARCHAR",
        "Description": "Manufacturer of the device"
      },
      {
        "ColumnName": "MODEL",
        "DataType": "VARCHAR",
        "Description": "Model of the device"
      },
      {
        "ColumnName": "SERIAL_NUMBER",
        "DataType": "VARCHAR",
        "Description": "Serial number of the device"
      },
      {
        "ColumnName": "PURCHASE_DATE",
        "DataType": "DATE",
        "Description": "Date when the device was purchased"
      },
      {
        "ColumnName": "FIRMWARE_VERSION",
        "DataType": "VARCHAR",
        "Description": "Firmware version of the device"
      },
      {
        "ColumnName": "LAST_SYNC_TIME",
        "DataType": "DATETIME",
        "Description": "Last sync time of the device"
      },
      {
        "ColumnName": "BATTERY_LEVEL",
        "DataType": "INTEGER",
        "Description": "Battery level of the device"
      },
      {
        "ColumnName": "STATUS",
        "DataType": "VARCHAR",
        "Description": "Status of the device"
      },
      {
        "ColumnName": "LOCATION",
        "DataType": "VARCHAR",
        "Description": "Location of the device"
      }
    ],
    "Relationships": [
      {
        "ForeignKey": "PATIENT_ID",
        "ReferencedTable": "D_Patients_v3",
        "ReferencedColumn": "PATIENT_ID"
      }
    ]
  }
]


# # Define your global database model
# global_database_model = {
#     "tables": table_descriptions,
#     "rules": json_rules
# }

