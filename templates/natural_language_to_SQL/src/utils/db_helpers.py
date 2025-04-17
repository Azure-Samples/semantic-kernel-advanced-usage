import sys
sys.path.append("../../")
import sqlite3
import os
import pyodbc
import json
import time
import struct
from decimal import Decimal
from dotenv import load_dotenv
from azure.identity import AzureCliCredential

# Custom JSON encoder to handle Decimal and date types
class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        # Handle datetime.date objects
        elif hasattr(obj, 'isoformat'):
            return obj.isoformat()
        return super(DecimalEncoder, self).default(obj)

# Load environment variables from .env file
load_dotenv()

#####################################################
## IMPORTANT: This is a SQLITE specific function. ##
## Generate your own for other databases.         ##
#####################################################

# Run in SQLite the SQL statement
# SQLite_DbName = 'telco_hgu_2.db'
SQLite_DbName = 'healthcare_data.db'
db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../../")


def SQLite_exec_sql(sql):
    """Execute SQL query and return results in a standardized format."""
    if sql is None:
        return None

    print("Accesing Database", os.path.join(db_path, SQLite_DbName))
    sql = sql.replace('REC.', 'REC_')  # SQLite does not support . in the column names
    try:
        conn = sqlite3.connect(os.path.join(db_path, SQLite_DbName))
        cursor = conn.cursor()

        print(f"* Running SQL in SQLite ['{sql}']...\n")
        cursor.execute(sql)
        rows = cursor.fetchall()
        
        # Get column names from cursor description
        columns = [desc[0] for desc in cursor.description]
        
        # Convert rows to list of dicts
        result = []
        for row in rows:
            row_dict = {}
            for i, value in enumerate(row):
                row_dict[columns[i]] = value
            result.append(row_dict)
            print(row)  # Print each row for debugging
        
        cursor.close()
        conn.close()
        
        return {"result": result}

    except Exception as ex:
        print(f'SQLite_exec_sql ERROR: {ex}')
        return {"error": str(ex)}


def write_to_file(text, text_filename, mode='a'):
    """Write text content to a file."""
    try:
        print(f"Writing file to full path: {os.path.abspath(text_filename)}")
        if isinstance(text_filename, str):
            text_filename = text_filename.replace("\\", "/")
        with open(text_filename, mode, encoding='utf-8') as file:
            file.write(text)
    except Exception as e:
        print(f"SERIOUS ERROR: Error writing text to file: {e}")


#####################################################
## Azure SQL Database with Entra ID authentication ##
#####################################################

# Azure SQL Database connection parameters from environment variables
AZURE_SQL_SERVER = os.getenv("AZURE_SQL_SERVER", "myazsqlsv.database.windows.net")
AZURE_SQL_DATABASE = os.getenv("AZURE_SQL_DATABASE", "adventureworks")
AZURE_SQL_USERNAME = os.getenv("AZURE_SQL_USERNAME", None)
AZURE_SQL_PASSWORD = os.getenv("AZURE_SQL_PASSWORD", None)
# Number of connection retries and wait time between retries
AZURE_SQL_MAX_RETRIES = 4
AZURE_SQL_RETRY_WAIT_SECONDS = 15

def azure_sql_exec_sql(sql):
    """Execute SQL query against Azure SQL Database and return results in a standardized format."""
    if sql is None:
        return None    # Connection retry logic
    retry_count = 0
    auth_retry_count = 0  # Track retries for the same auth method
    last_error = None
    current_auth_method = None  # Track which auth method we're currently using
    
    while retry_count < AZURE_SQL_MAX_RETRIES:
        try:
            # Track which authentication method we're about to try
            auth_method = ""
            connection_string = None
            
            # First attempt: Use Azure CLI Credential token-based auth (same as in notebook)
            if retry_count == 0 or (current_auth_method == "Azure CLI Credential Token" and auth_retry_count < AZURE_SQL_MAX_RETRIES - 1):
                try:
                    # Get the access token using Azure CLI
                    credential = AzureCliCredential()
                    token = credential.get_token("https://database.windows.net/").token
                    
                    # Prepare the token for ODBC
                    token_bytes = bytes(token, "UTF-8")
                    expanded_token = b"".join([bytes([b]) + b"\x00" for b in token_bytes])
                    token_struct = struct.pack("=i", len(expanded_token)) + expanded_token
                    
                    # Connection string
                    connection_string = (
                        f"Driver={{ODBC Driver 18 for SQL Server}};"
                        f"Server={AZURE_SQL_SERVER};"
                        f"Database={AZURE_SQL_DATABASE};"
                        "Encrypt=yes;"
                        "TrustServerCertificate=no;"
                        "Connection Timeout=60;"
                    )
                    
                    auth_method = "Azure CLI Credential Token"
                    current_auth_method = auth_method
                    
                    # Connect with token
                    conn = pyodbc.connect(connection_string, attrs_before={1256: token_struct})
                except Exception as ex:
                    print(f"Azure CLI token authentication failed: {ex}")
                    # If token auth fails, continue to next auth method
                    connection_string = None
            
            # Second attempt: Use SQL Authentication if credentials provided
            elif connection_string is None and (current_auth_method == "SQL Authentication" and auth_retry_count < AZURE_SQL_MAX_RETRIES - 1) or (current_auth_method != "SQL Authentication" and AZURE_SQL_USERNAME and AZURE_SQL_PASSWORD):
                connection_string = (
                    f"Driver={{ODBC Driver 18 for SQL Server}};"
                    f"Server={AZURE_SQL_SERVER};"
                    f"Database={AZURE_SQL_DATABASE};"
                    f"UID={AZURE_SQL_USERNAME};"
                    f"PWD={AZURE_SQL_PASSWORD};"
                    "TrustServerCertificate=yes;"
                )
                auth_method = "SQL Authentication"
                current_auth_method = auth_method
                conn = pyodbc.connect(connection_string)
            
            # Third attempt: Entra ID Default Authentication
            elif connection_string is None and ((current_auth_method == "Entra ID Default" and auth_retry_count < AZURE_SQL_MAX_RETRIES - 1) or (current_auth_method != "Entra ID Default" and current_auth_method != "SQL Authentication")):
                connection_string = (
                    f"Driver={{ODBC Driver 18 for SQL Server}};"
                    f"Server={AZURE_SQL_SERVER};"
                    f"Database={AZURE_SQL_DATABASE};"
                    "Authentication=ActiveDirectoryIntegrated;"
                    "TrustServerCertificate=yes;"
                )
                auth_method = "Entra ID Default"
                current_auth_method = auth_method
                conn = pyodbc.connect(connection_string)
            
            # Fallback: Entra ID Interactive Authentication
            elif connection_string is None:
                connection_string = (
                    f"Driver={{ODBC Driver 18 for SQL Server}};"
                    f"Server={AZURE_SQL_SERVER};"
                    f"Database={AZURE_SQL_DATABASE};"
                    "Authentication=ActiveDirectoryInteractive;"
                    "TrustServerCertificate=yes;"
                )
                auth_method = "Entra ID Interactive"
                current_auth_method = auth_method
                conn = pyodbc.connect(connection_string)
            
            print(f"Connecting to Azure SQL Database: {AZURE_SQL_SERVER}, {AZURE_SQL_DATABASE} (Attempt {retry_count + 1}/{AZURE_SQL_MAX_RETRIES}, Auth method: {auth_method}, Auth retry: {auth_retry_count + 1})")
            
            cursor = conn.cursor()

            print(f"* Running SQL in Azure SQL [{sql}]...\n")
            cursor.execute(sql)
            rows = cursor.fetchall()
            
            # Get column names from cursor description
            columns = [desc[0] for desc in cursor.description]
            
            # Convert rows to list of dicts
            result = []
            for row in rows:
                row_dict = {}
                for i, value in enumerate(row):
                    row_dict[columns[i]] = value
                result.append(row_dict)
                print(row)  # Print each row for debugging
            
            cursor.close()
            conn.close()
            
            # If we reach here, the connection and query succeeded
            return {"result": result}        
        except Exception as ex:
            last_error = ex            
            error_str = str(ex).lower()
            
            # Check if this is a timeout error    
            is_timeout_error = any(timeout_text in error_str for timeout_text in [
                "timeout", "timed out", "connection timeout", 
                "operation timed out", "request timed out"
            ]) or "258" in error_str  # Error code 258 is a timeout error
              
            # Check if this is an authentication error
            is_auth_error = any(auth_text in error_str for auth_text in [
                "login failed", "authentication failed", "access denied", 
                "user is not associated", "token", "credential", "permission", 
                "authorization", "not authorized", "invalid auth", "ailed to authenticate the user"
            ])
            
            # Check specifically for WIA (Windows Integrated Authentication) failures
            is_wia_error = ("adal received an empty response" in error_str and "wia flow" in error_str) or \
                            ("authentication option is 'activedirectoryintegrated'" in error_str) or \
                            ("0xcaa9003b" in error_str)
              # Check if this is a syntax error or other SQL execution error
            is_sql_syntax_error = any(syntax_text in error_str for syntax_text in [
                "syntax error", "incorrect syntax", "invalid column name", 
                "invalid object name", "invalid identifier", "sql error", 
                "database error", "procedure or function", "statement is not valid"
            ])
            
            # For SQL syntax errors, exit immediately as retrying won't help
            if is_sql_syntax_error:
                print(f"SQL syntax or execution error detected: {ex}")
                # Return error for SQL regeneration rather than retrying authentication
                return {"error": str(ex), "error_type": "sql_syntax"}
                
            # Update the retry counters appropriately
            # Global retry count - overall attempts
            retry_count += 1
            
            # For each authentication method, we'll allow up to MAX_RETRIES_PER_METHOD (4 in this case)
            # before moving to the next method
            MAX_RETRIES_PER_METHOD = 4
            
            # For timeout errors, retry the same authentication method
            if is_timeout_error:
                auth_retry_count += 1
                
                if auth_retry_count < MAX_RETRIES_PER_METHOD:
                    # Stay with the same auth method
                    print(f"Connection timeout (Method {current_auth_method}, Attempt {auth_retry_count}/{MAX_RETRIES_PER_METHOD}, Total {retry_count}/{AZURE_SQL_MAX_RETRIES}): {ex}")
                    print(f"Database may be waking up from suspended mode. Retrying same method in {AZURE_SQL_RETRY_WAIT_SECONDS} seconds...")
                    time.sleep(AZURE_SQL_RETRY_WAIT_SECONDS)
                    
                    # Don't change current_auth_method - we'll retry the same one
                    # Adjust the retry_count to give the current method more attempts
                    if retry_count >= AZURE_SQL_MAX_RETRIES:
                        retry_count = AZURE_SQL_MAX_RETRIES - 1  # Give it one more chance
                else:
                    # Max retries for this method reached, try next method
                    print(f"Max retries ({MAX_RETRIES_PER_METHOD}) for method {current_auth_method} reached. Trying next method.")
                    auth_retry_count = 0  # Reset for next method
                    
                    # Automatically skip WIA if the current method is Azure CLI Token
                    if current_auth_method == "Azure CLI Credential Token" and AZURE_SQL_USERNAME and AZURE_SQL_PASSWORD:
                        current_auth_method = "SQL Authentication"
                    elif current_auth_method == "Azure CLI Credential Token" or current_auth_method == "SQL Authentication":
                        # Skip WIA entirely due to known issues
                        current_auth_method = "Entra ID Interactive" 
                    elif current_auth_method == "Entra ID Default":
                        current_auth_method = "Entra ID Interactive"
                    else:
                        print(f"All authentication methods exhausted after {retry_count} total attempts.")
                        break
            
            # For WIA errors, skip this auth method entirely
            elif is_wia_error:
                print(f"Windows Integrated Authentication (WIA) failed: {ex}")
                print(f"This is a known issue with WIA. Skipping to next authentication method...")
                
                # Skip to interactive auth immediately
                current_auth_method = "Entra ID Interactive"
                auth_retry_count = 0  # Reset for the new method
                
                if retry_count >= AZURE_SQL_MAX_RETRIES:
                    print(f"All authentication methods failed after WIA error. Giving Interactive Auth one last chance.")
                    retry_count = AZURE_SQL_MAX_RETRIES - 1  # Give it one more chance
                
            # For authentication errors, move to next method immediately
            elif is_auth_error:
                print(f"Authentication failed with method {current_auth_method}: {ex}")
                
                # Reset auth_retry_count for new method and change method
                auth_retry_count = 0
                
                if current_auth_method == "Azure CLI Credential Token" and AZURE_SQL_USERNAME and AZURE_SQL_PASSWORD:
                    current_auth_method = "SQL Authentication"
                    print("Trying SQL Authentication...")
                elif current_auth_method == "Azure CLI Credential Token" or current_auth_method == "SQL Authentication":
                    # Skip WIA entirely due to known issues
                    current_auth_method = "Entra ID Interactive"
                    print("Trying Entra ID Interactive Authentication...")
                elif current_auth_method == "Entra ID Default":
                    current_auth_method = "Entra ID Interactive"
                    print("Trying Entra ID Interactive Authentication...")
                else:
                    print(f"All authentication methods exhausted after {retry_count} total attempts.")
                    break
                    
                if retry_count >= AZURE_SQL_MAX_RETRIES:
                    print(f"All authentication methods exceeded max retries. Giving {current_auth_method} one last chance.")
                    retry_count = AZURE_SQL_MAX_RETRIES - 1  # Give it one more chance
              # Check for XML data type comparison error specifically
            elif "xml data type cannot be compared or sorted" in error_str or "42000" in error_str:
                print(f"XML data type comparison error detected: {ex}")
                # Return error for SQL regeneration rather than retrying authentication
                return {"error": str(ex), "error_type": "sql_syntax"}
                
            # For other unclassified errors
            else:
                auth_retry_count += 1
                print(f"Unknown error occurred with method {current_auth_method} (Retry {auth_retry_count}/{MAX_RETRIES_PER_METHOD}): {ex}")
                
                if auth_retry_count >= MAX_RETRIES_PER_METHOD or retry_count >= AZURE_SQL_MAX_RETRIES:
                    # Try next method
                    auth_retry_count = 0
                    
                    if current_auth_method == "Azure CLI Credential Token" and AZURE_SQL_USERNAME and AZURE_SQL_PASSWORD:
                        current_auth_method = "SQL Authentication"
                        print("Trying SQL Authentication...")
                    elif current_auth_method == "Azure CLI Credential Token" or current_auth_method == "SQL Authentication":
                        # Skip WIA entirely due to known issues
                        current_auth_method = "Entra ID Interactive"
                        print("Trying Entra ID Interactive Authentication...")
                    elif current_auth_method == "Entra ID Default":
                        current_auth_method = "Entra ID Interactive"
                        print("Trying Entra ID Interactive Authentication...")
                    else:
                        print(f"All authentication methods exhausted after {retry_count} total attempts.")
                        break
                else:
                    # Wait before retrying the same method
                    time.sleep(AZURE_SQL_RETRY_WAIT_SECONDS)
    
    # If all retries failed, return the error
    print(f'azure_sql_exec_sql ERROR after {retry_count} attempts: {last_error}')
    return {"error": str(last_error)}


def get_adventureworks_metadata():
    """
    Retrieve metadata from AdventureWorks database including extended properties.
    Returns a structured data model suitable for the application.
    """
    metadata_sql = """
    WITH TableInfo AS (
        SELECT 
            t.object_id AS table_id,
            SCHEMA_NAME(t.schema_id) AS schema_name,
            t.name AS table_name,
            CAST(ep.value AS NVARCHAR(MAX)) AS table_description
        FROM 
            sys.tables t
        LEFT JOIN 
            sys.extended_properties ep ON ep.major_id = t.object_id AND ep.minor_id = 0 AND ep.name = 'MS_Description'
        WHERE 
            t.is_ms_shipped = 0
    ),
    ColumnInfo AS (
        SELECT 
            c.object_id AS table_id,
            c.column_id,
            c.name AS column_name,
            t.name AS data_type,
            CAST(ep.value AS NVARCHAR(MAX)) AS column_description
        FROM 
            sys.columns c
        JOIN 
            sys.types t ON c.user_type_id = t.user_type_id
        LEFT JOIN 
            sys.extended_properties ep ON ep.major_id = c.object_id AND ep.minor_id = c.column_id AND ep.name = 'MS_Description'
        WHERE 
            c.is_hidden = 0
    ),
    ForeignKeyInfo AS (
        SELECT 
            fk.parent_object_id AS table_id,
            COL_NAME(fkc.parent_object_id, fkc.parent_column_id) AS foreign_key_column,
            OBJECT_NAME(fk.referenced_object_id) AS referenced_table,
            COL_NAME(fkc.referenced_object_id, fkc.referenced_column_id) AS referenced_column
        FROM 
            sys.foreign_keys fk
        JOIN 
            sys.foreign_key_columns fkc ON fk.object_id = fkc.constraint_object_id
    )
    SELECT 
        ti.schema_name,
        ti.table_name,
        ti.table_description,
        ci.column_name,
        ci.data_type,
        ci.column_description,
        fki.foreign_key_column,
        fki.referenced_table,
        fki.referenced_column
    FROM 
        TableInfo ti
    LEFT JOIN 
        ColumnInfo ci ON ti.table_id = ci.table_id
    LEFT JOIN 
        ForeignKeyInfo fki ON ti.table_id = fki.table_id AND ci.column_name = fki.foreign_key_column
    ORDER BY 
        ti.schema_name, ti.table_name, ci.column_id
    """
    
    result = azure_sql_exec_sql(metadata_sql)
    
    if not result or "error" in result:
        print(f"Error fetching metadata: {result.get('error', 'Unknown error')}")
        return None
    
    # Process the results into the format required by data_model.py
    tables_dict = {}
    
    for row in result["result"]:
        schema_name = row["schema_name"]
        table_name = row["table_name"]
        full_table_name = f"{schema_name}.{table_name}"
        
        # Initialize table entry if not exists
        if full_table_name not in tables_dict:
            tables_dict[full_table_name] = {
                "TableName": full_table_name,
                "Description": row["table_description"] or f"Table {full_table_name} in AdventureWorks database",
                "Columns": [],
                "Relationships": []
            }
        
        # Add column
        if row["column_name"]:
            column = {
                "ColumnName": row["column_name"],
                "DataType": row["data_type"],
                "Description": row["column_description"] or f"Column {row['column_name']} in table {full_table_name}"
            }
            tables_dict[full_table_name]["Columns"].append(column)
        
        # Add relationship
        if row["foreign_key_column"] and row["referenced_table"]:
            relationship = {
                "ForeignKey": row["foreign_key_column"],
                "ReferencedTable": row["referenced_table"],
                "ReferencedColumn": row["referenced_column"]
            }
            # Check if this relationship already exists before adding
            if relationship not in tables_dict[full_table_name]["Relationships"]:
                tables_dict[full_table_name]["Relationships"].append(relationship)
    
    # Convert dictionary to list of tables
    table_descriptions = list(tables_dict.values())
    
    # Generate and return the structured metadata
    return table_descriptions


def generate_data_model():
    """
    Generate the data model file for AdventureWorks database.
    """
    table_descriptions = get_adventureworks_metadata()
    
    if not table_descriptions:
        print("Failed to retrieve metadata from AdventureWorks")
        return False
    
    # Create a basic version of json_rules
    json_rules = """
  "rules": [
    {{
      "id": "AW1",
      "name": "Sales Order Filtering",
      "condition": "Look for sales orders in the question '{question}'.",
      "action": "You will need to query tables in the Sales schema such as Sales.SalesOrderHeader and Sales.SalesOrderDetail."
    }},
    {{
      "id": "AW2",
      "name": "Product Information",
      "condition": "Check if the question '{question}' is asking about products.",
      "action": "Focus on the Production.Product table and related tables like Production.ProductCategory and Production.ProductSubcategory."
    }},
    {{
      "id": "AW3",
      "name": "Customer Information",
      "condition": "Look for customer data in the question '{question}'.",
      "action": "Consider using the Sales.Customer table joined with Person.Person for individual customers or Sales.Store for store customers."
    }},
    {{
      "id": "AW4",
      "name": "Employee Information",
      "condition": "The question '{question}' is about employees or staff.",
      "action": "Query the HumanResources.Employee table joined with Person.Person for detailed employee information."
    }},
    {{
      "id": "AW5",
      "name": "Date Handling",
      "condition": "The question '{question}' involves date ranges or time periods.",
      "action": "Use date functions on columns like OrderDate, DueDate, or ModifiedDate as appropriate. Consider using DATEADD, DATEDIFF, or BETWEEN for date ranges."
    }}
  ]
"""
    
    # Format the data model file content
    data_model_content = f"""table_descriptions = {json.dumps(table_descriptions, indent=2)}


json_rules = {json_rules}


global_database_model = {json.dumps(table_descriptions, indent=2)}
"""
    
    # Write to the data model file
    model_file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 
                                  "../constants/data_model.py")
    
    write_to_file(data_model_content, model_file_path, mode='w')
    print(f"Data model generated at: {model_file_path}")
    return True


# Uncomment to generate data model on module import
# generate_data_model()