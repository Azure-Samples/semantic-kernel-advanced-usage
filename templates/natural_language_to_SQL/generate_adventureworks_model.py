#!/usr/bin/env python
"""
Script to generate the data model for the AdventureWorks database.
This script will connect to the Azure SQL database, retrieve schema metadata,
and generate a data_model.py file that can be used by the natural language to SQL application.
"""

from src.utils import generate_data_model

if __name__ == "__main__":
    print("Generating AdventureWorks data model...")
    success = generate_data_model()
    
    if success:
        print("✅ Data model successfully generated!")
        print("The AdventureWorks schema has been extracted with all tables, columns, and relationships.")
        print("The data model is ready for use with the natural language to SQL application.")
    else:
        print("❌ Failed to generate data model.")
        print("Please check your Azure SQL connection and permissions.")
        print("Make sure you have the ODBC Driver 18 for SQL Server installed.")
        print("Make sure you are authenticated with Entra ID (Azure AD).")