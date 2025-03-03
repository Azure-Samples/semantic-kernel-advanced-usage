import sys
sys.path.append("../../")
import sqlite3
import pandas as pd
import os


#####################################################
## IMPORTANT: This is a SQLITE specific function. ##
## Generate your own for other databases.         ##
#####################################################

# Run in SQLite the SQL statement
SQLite_DbName = 'telco_hgu_2.db'
# SQLite_DbName = 'healthcare_data.db'

def SQLite_exec_sql(sql):
    """Execute SQL query and return results in a standardized format."""
    if sql is None:
        return None

    sql = sql.replace('REC.', 'REC_')  # SQLite does not support . in the column names
    try:
        conn = sqlite3.connect(SQLite_DbName)
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