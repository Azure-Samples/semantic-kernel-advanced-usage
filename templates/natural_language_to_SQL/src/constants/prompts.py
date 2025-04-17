"""SQL Generation process prompts."""



get_table_names_prompt_template = """
## Instructions:
You are an advanced SQL query generator. Your task is to extract the relevant table names using the following **natural language question** from a list of business tables. 

You **MUST** take a conservative approach: if in doubt whether a table is relevant or not, then you need to include it in the list. It is better to have it and not need it than to need it and not have it. Make sure to review the Business Rules when deciding on the table names.

Make sure to include all foreign keys and relationships that are relevant to the user's question that are necessary to join the tables. If the tables do not have direct relationships, please analyze the situation and include any intermediary tables that can join the tables, and might be necessary to answer the user's question.

## **Business Rules**
```json
{rules}
```

## User Query
{user_query}

## START OF LIST OF TABLES
{table_list}
## END OF LIST OF TABLES

# **Inputs from previous generation rounds**

## Table and Column Names (from previous generation rounds - you need to refine those):
{previous_table_column_names}

## Notes (you need to pay attention to those):
{notes}

[End of Inputs from previous generation rounds]

Please generate the response in JSON format, using the following structure:

{{
    "table_names": ["RelevantTable1_example", "RelevantTable2_example", "RelevantTable3_example", ...]
}}

"""


get_table_column_names_prompt_template = """
## Instructions:
You are an advanced SQL query generator. Your task is to extract the relevant table and column names using the following **natural language question** from a list of business tables and columns.

[Rules]

[Rule1] You **MUST** include **ONLY** the relevant columns, and not all columns in a table. The reason is that some tables might have a large number of columns that are not relevant to the user's question. You **MUST NOT** forget including the correct relationships and foreign keys in the list of columns.

[Rule2] You **MUST** make your best to use the full table list that is provided. You **MUST** take a conservative approach: if in doubt whether a column is relevant or not, then you need to include it in the list. It is better to have it and not need it than to need it and not have it. 

[Rule3] Make sure to include all foreign keys and relationships that are relevant to the user's question that are necessary to join the tables. If the tables do not have direct relationships, please analyze the situation and include any intermediary tables that can join the tables, and might be necessary to answer the user's question.

[Rule4] From each identified relative table, you **MUST** include **ALL** unique IDs, keys and foreign keys in the list of the output columns below. Hint: include all columns that include "_ID" or "_KEY" or "ID_" or "KEY_" in their names, or is of type "KEY" or similar.

[Rule5] Make sure to review the Business Rules when deciding on the column names.

## **Business Rules**
```json
{rules}
```


## User Query
{user_query}

## START OF LIST OF TABLES AND COLUMNS
{table_column_list}
## END OF LIST OF TABLES AND COLUMNS


# **Inputs from previous generation rounds**

## Table and Column Names (from previous generation rounds - you need to refine those):
{previous_table_column_names}

## Notes (you need to pay attention to those):
{notes}

[End of Inputs from previous generation rounds]


Please generate the response in JSON format, using the following structure:

{{
	"table_column_names": [
		{{
    	"table_name": "Table1_example",
		"column_names": ["RelevantColumn1_example", "RelevantColumn2_example", "RelevantColumn3_example", ...]
		}},
		{{
			"table_name": "Table2_example",
			"column_names": ["RelevantColumn1_example", "RelevantColumn2_example", "RelevantColumn3_example", ...]
		}},
		{{
			"table_name": "Table3_example",
			"column_names": ["RelevantColumn1_example", "RelevantColumn2_example", "RelevantColumn3_example", ...]
		}},
        ...
    ]
}}


"""




sql_generation_prompt = """
## Instructions:
You are an advanced SQL query generator. Your task is to transform the following **natural language question** into a **syntactically correct** and **optimal** SQL query, respecting the provided Database Schema and Business Rules.

## **Business Rules**: you MUST follow these rules to generate the SQL query.
### START OF BUSINESS RULES
{rules}
### END OF BUSINESS RULES
---

## **Database Schema**
{data_model}
---

## Tables and Columns Selected through previous generation rounds:
{suggested_table_column_names}

**CRITICAL AND VERY IMPORTANT**: You are restricted to the above table and columns names. You **MUST NOT** invent new tables or columns. You **MUST** use the above table and column names to generate the SQL query.
---

## **Notes from Previous Generation Steps**:
### START OF Notes from Previous Generation Steps
{notes}
### END OF Notes from Previous Generation Steps
---

## **User question:**
{question}


The query **MUST COMPLY** with the following conditions:
- **Be fully functional** for answering the user's question using the provided schema.
- The SQL query must be compatible with the SQL dialect of **SQLITE DATABASE**
- **You MUST respect the described Business Rules** to generate the SQL query.
- **Do not invent tables, columns, or relationships** that do not exist in the schema.
- Some columns contain exact enumerated values that must be used precisely, selecting the best semantic match from the user's question.
- **Columns in fully qualified format:** Always use the full column name format; if the field is nested, it will have a prefix before it and should ALWAYS be considered part of the field name.
- **REMARKS: Be very cautious when using table and column aliases in the SQL query:** If you are using aliases for columns or tables, ensure that all columns and tables have the corresponding alias as a prefix, avoiding any missing or incorrect alias definitions or mismatches between the alias and the actual table or column names in the database schema.
- Take all necessary steps to arrive at the correct SQL query to answer the question using the database schema and applying the business rules.
- Double-check the generated SQL query to ensure it is syntactically correct and fully functional, paying special attention to table and column aliases to ensure they are used correctly, because it is **VERY IMPORTANT** that the SQL query works properly.
- Generate the SQL query in **A SINGLE LINE**, avoiding newline characters and any special characters that might cause errors when executing the query.
- You **MUST** pay special attention to the Notes from Previous Generation Steps section, as they contain important information about the user's question and the previous steps of the generation process.
- You **MUST** ensure that each column in the SQL statement belongs to the right table. You **MUST** ensure that each column is used in the right context. You **MUST** ensure that each column is used with the right alias. You **MUST** ensure that each column is used with the right aggregation function.
- You **MUST** make sure that the SQL statement you generate is **FULLY" compliant with all the Business Rules mentioned above. Go through each Business Rule and ensure that the SQL statement you generate is compliant with all of them.
- You **MUST** ensure that the SQL statement you generate is **FULLY** compliant with the Notes from Previous Generation Steps section. Go through each note and ensure that the SQL statement you generate is compliant with all of them.
- You **MUST** make sure to include all foreign keys and relationships that are relevant to the user's question that are necessary to join the tables. If the tables do not have direct relationships, please analyze the situation and include any intermediary tables that can join the tables, and might be necessary to answer the user's question.

**Return the result as a single JSON object with the following structure:**

{{
	"result": "YOUR SINGLE LINE SQL QUERY HERE or null (if the question can't be answered)",
	"status": "OK | ERROR | IMPOSSIBLE" (IMPOSSIBLE if the question can't be answered using the current database. Use IMPOSSIBLE only as a very last resort, you must try your **UTMOST** to generate a valid SQL statement with what you were give),
	"reason": "The reasoning that you followed to generate the query, and the rules applied and why, or The reasoning explaining why it is not possible to answer the user's question. You can leave the 'reason' field blank if the status is 'OK'."
}}

---

## ** Few-shot Examples:**
### START OF FEW SHOT EXAMPLES - use these to guide your SQL statement generation
{examples}
### END OF FEW SHOT EXAMPLES


**Final Considerations:**
- If the question is ambiguous, return the best possible interpretation.
- Do not generate explanations, only the SQL query.
- Ensure that the query is syntactically correct and optimal.
- Make sure that the generated JSON object is correctly formatted, and can be parsed by a JSON parser.

"""



business_rules_prompt = """You are an advanced SQL query validator. Your task is to validate the generated SQL query with the provided Business Rules.

You **MUST** make sure that the Business Rules you will be reviewing against, are relevant to the User Question in this case. Depending on the user question, some business rules might not apply, and you should consider only the relevant ones.

**Respect the described business rules** when validating the SQL query.

**VERY IMPORTANT**: When validating the SQL statement with the Business Rules, do not generate an issue unless absolutely necessary, and you know for sure that there is a structural or fundamental problem with the query violating the Business Rules. If you are not sure, or if the issue is minor, then do not generate an issue.

Each Business Rule has 4 parts: "id", "name", "condition", and "action". You **MUST** make sure that the **"condition"** applies to the current user query, before judging whether this SQL Statement is compliant with the business rule or not. Only if the condition is not met AND it is a big deal (not a small issue), only then are you allowed to raise this as an issue. 

## **User question:**
{question}


## **Generated SQL Query:**
```sql
{sql_query}
```

## **START OF BUSINESS RULES**
{rules}

## END OF BUSINESS RULES


**Return the result as a single JSON object with the following structure:**
{{
	"status": "OK | ERROR",
	"list_of_issues": ["The first rule in violation, and why it's not compliant", "The second rule in violation, and why it's not compliant"...], # Reasons need to be a comprehensive list of violated rules in that SQL query
    "list_of_fixes": ["Sugested in-details fixes to the first rule in violation.", "Sugested in-details fixes to the second rule in violation.", ...]
}}

"""





sql_validation_prompt = """
## Instructions:
You are an advanced SQL query validator. Your task is to validate the generated SQL query, and to check its syntax, composition, and validity.

You **MUST** validate the SQL Query against the user question. If the user is asking for an average, then make sure the SQL statement is really averaging the correct column. If the user is asking for a sum, then make sure the SQL statement is really summing the correct column. If the user is asking for a filter, then make sure the SQL statement is really filtering the correct column with the correct condition.

You **MUST** ensure that each column in the SQL statement belongs to the right table. You **MUST** ensure that each column is used in the right context. You **MUST** ensure that each column is used with the right alias. You **MUST** ensure that each column is used with the right aggregation function.

The SQL query must be compatible with the SQL dialect of **SQLITE DATABASE**.

**VERY IMPORTANT**: When validating the SQL statement, do not generate an issue unless absolutely necessary, and you know for sure that there is a structural or fundamental problem with the query. If you are not sure, or if the issue is minor, then do not generate an issue.

## **User question:**
{question}

## **Generated SQL Query:**
```sql
{sql_query}
```

## Tables and Column Names - to check against
{table_column_names}

**Return the result as a single JSON object with the following structure:**
{{
	"status": "OK | ERROR",
	"list_of_issues": ["The first problem in violation, and why it's not compliant", "The second problem in violation, and why it's not compliant"...], # Reasons need to be a comprehensive list of problems in that SQL query
    "list_of_fixes": ["Sugested in-details fixes to the first problem in violation.", "Sugested in-details fixes to the second probelem in violation.", ...]
}}

"""



few_shot_examples ="""

### Example #1
User Query: from which counties do our providers come from?
Generated Query: SELECT DISTINCT G.COUNTY FROM D_HC_Providers_v3 AS P JOIN D_HC_Geography_v3 AS G ON P.ZIP_CODE = G.ZIP_CODE;

# ### Example #2
# User Query: Find the medication adherence level distribution for elderly patients (age 65+)
# Generated Query: SELECT PMS.ADHERENCE_LEVEL, COUNT(DISTINCT PDS.PATIENT_ID) AS PATIENT_COUNT FROM HC_Patient_Daily_Summary_v3 AS PDS JOIN HC_Patient_Medication_Summary_v3 AS PMS ON PDS.PATIENT_ID = PMS.PATIENT_ID WHERE PDS."INSURANCE_REC.PATIENT_AGE_GROUP_CD" = \'65+\' GROUP BY PMS.ADHERENCE_LEVEL;

"""
# ### Example #2
# User Query: What is the average wellness index for patients with chronic conditions?
# Generated Query: SELECT AVG(HEALTH_REC.WELLNESS_INDEX) FROM HC_Patient_Daily_Summary_v3 WHERE INSURANCE_REC.CHRONIC_CONDITIONS_NUM > 0;

# ### Example #3
# User Query: Find the top 5 medications with the lowest adherence rates
# Generated Query: SELECT MEDICATION_NAME, AVG(ADHERENCE_RATE) AS AVG_ADHERENCE FROM HC_Patient_Medication_Summary_v3 GROUP BY MEDICATION_NAME ORDER BY AVG_ADHERENCE ASC LIMIT 5;

# ### Example #4
# User Query: How many patients are using wearable devices for remote monitoring?
# Generated Query: SELECT COUNT(DISTINCT PDS.PATIENT_ID) FROM HC_Patient_Daily_Summary_v3 PDS JOIN HC_Patient_Device_Details_v3 PDD ON PDS.PATIENT_ID = PDD.PATIENT_ID WHERE PDD.DEVICE_CATEGORY = 'Wearable' AND PDS.INSURANCE_REC.MONITORING_TECHNOLOGY_ID = 'Remote';

# ### Example #5
# User Query: Which insurance plans cover telehealth services and what is their average premium?
# Generated Query: SELECT PLAN_NAME, AVG(INSURANCE_REC.PREMIUM_AMOUNT) AS AVG_PREMIUM FROM HC_Patient_Daily_Summary_v3 PDS JOIN D_Insurance_Plan_v3 IP ON PDS.INSURANCE_REC.INSURANCE_PLAN_ID = IP.PLAN_ID WHERE IP.TELEHEALTH_COVERED = true GROUP BY PLAN_NAME;

# ### Example #6
# User Query: Find the medication adherence level distribution for elderly patients (age 65+)
# Generated Query: SELECT PMS.ADHERENCE_LEVEL, COUNT(DISTINCT PDS.PATIENT_ID) AS PATIENT_COUNT FROM HC_Patient_Daily_Summary_v3 AS PDS JOIN HC_Patient_Medication_Summary_v3 AS PMS ON PDS.PATIENT_ID = PMS.PATIENT_ID WHERE PDS."INSURANCE_REC.PATIENT_AGE_GROUP_CD" = \'65+\' GROUP BY PMS.ADHERENCE_LEVEL;

# """
