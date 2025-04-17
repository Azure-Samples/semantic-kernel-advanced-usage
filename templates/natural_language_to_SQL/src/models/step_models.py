import sys
sys.path.append("../../")

from pydantic import BaseModel, Field
from typing import List, Any, Union, Literal, Optional


# Structured Outputs Models

class ValidTableName(BaseModel):
    table_name: str  # Allow any table name instead of a restricted list


class GetTableNames(BaseModel):
    table_names: List[Union[ValidTableName, dict, str]]
    
    def __init__(self, **data):
        # Convert string table names to ValidTableName objects
        if "table_names" in data and isinstance(data["table_names"], list):
            for i, item in enumerate(data["table_names"]):
                if isinstance(item, str):
                    data["table_names"][i] = ValidTableName(table_name=item)
                elif isinstance(item, dict) and "table_name" not in item and len(item) == 1:
                    # Handle potential dict with a single value
                    key = list(item.keys())[0]
                    data["table_names"][i] = ValidTableName(table_name=item[key])
        super().__init__(**data)


class TableColumns(BaseModel):
    table_name: str
    column_names: List[str]


class GetColumnNames(BaseModel):
    table_column_list: Optional[List[TableColumns]] = None
    table_column_names: Optional[List[TableColumns]] = None
    
    def __init__(self, **data):
        # Handle both possible field names in the response
        if "table_column_names" in data and "table_column_list" not in data:
            data["table_column_list"] = data["table_column_names"]
        super().__init__(**data)
        
    @property
    def get_table_columns(self) -> List[TableColumns]:
        """Return whichever field is populated (table_column_list or table_column_names)"""
        return self.table_column_list or self.table_column_names or []


class SQLGenerateResult(BaseModel):
    sql_statement: Optional[str] = None
    result: Optional[str] = None
    status: Literal["OK", "ERROR", "IMPOSSIBLE"]
    reason: str
    
    def __init__(self, **data):
        # Handle both possible field names in the response
        if "result" in data and "sql_statement" not in data and isinstance(data["result"], str):
            data["sql_statement"] = data["result"]
        super().__init__(**data)
        
    @property
    def get_sql(self) -> str:
        """Return whichever field is populated (sql_statement or result)"""
        return self.sql_statement or self.result or ""


class ValidationResult(BaseModel):
    status: Literal["OK", "ERROR"]
    list_of_issues: List[str] = Field(default_factory=list)
    list_of_fixes: List[str] = Field(default_factory=list)
    
    def __str__(self) -> str:
        """Provide a string representation for error messages."""
        if self.status == "OK":
            return "Validation successful"
        else:
            issues = ", ".join(self.list_of_issues) if self.list_of_issues else "No specific issues mentioned"
            return f"Validation failed: {issues}"


# Step Inputs Models

class TableNamesStepInput(BaseModel):
    user_query: str
    table_column_names: Union[GetColumnNames, None] = None
    notes: Union[str, Any] = "No notes at this point."


class ColumnNamesStepInput(BaseModel):
    user_query: str
    table_names: GetTableNames
    table_column_names: Union[GetColumnNames, None] = None
    notes: Union[str, Any] = "No notes at this point."


class SQLGenerationStepInput(BaseModel):
    user_query: str
    table_column_names: GetColumnNames
    notes: Union[str, Any] = "No notes at this point."


class BusinessRulesStepInput(BaseModel):
    user_query: str
    table_column_names: GetColumnNames
    sql_generation_result: SQLGenerateResult


class ValidationStepInput(BaseModel):
    user_query: str
    table_column_names: GetColumnNames
    sql_statement: str


class ExecutionStepInput(BaseModel):
    """Input for execution step."""
    user_query: str
    table_column_names: GetColumnNames
    sql_statement: str
    table_names: Optional[GetTableNames] = None
    column_names: Optional[List[str]] = None
    response_filename: Optional[str] = None


class Execution2TableNames(BaseModel):
    """Model for execution error with table names."""
    user_query: str
    table_names: Optional[GetTableNames] = None
    column_names: Optional[List[str]] = None
    sql_statement: str
    error_description: str
    response_filename: Optional[str] = None
    
    def __init__(self, **data):
        # Handle cases where table_names might be missing or in different format
        if "table_names" in data and not isinstance(data["table_names"], GetTableNames):
            if isinstance(data["table_names"], dict) and "table_names" in data["table_names"]:
                data["table_names"] = GetTableNames(table_names=data["table_names"]["table_names"])
            elif isinstance(data["table_names"], list):
                data["table_names"] = GetTableNames(table_names=data["table_names"])
            elif data["table_names"] is None:
                data["table_names"] = GetTableNames(table_names=[])
        super().__init__(**data)
