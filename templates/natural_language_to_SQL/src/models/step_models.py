import sys
sys.path.append("../../")

from pydantic import BaseModel, Field
from typing import List, Any, Union, Literal, Optional


# Structured Outputs Models

class ValidTableName(BaseModel):
    table_name: Literal['CBD_Summary_HGU_Detail_Daily_v10',
                        'CBD_Summary_HGU_Stations_Daily_v10',
                        'D_CBD_Static_Geo_Area_v6',
                        'D_CBD_Static_Geo_Area_Level2_v6',
                        'D_CBD_Static_Geo_Area_Level3_v6',
                        'D_CBD_Static_Geo_Area_Level4_v6',
                        'D_CBD_Static_Station_Type_v6',
                        'D_Segment_v8',
                        'D_Fixed_Tariff_Plan_v8']


class GetTableNames(BaseModel):
    table_names: List[ValidTableName]


class TableColumns(BaseModel):
    table_name: str
    column_names: List[str]


class GetColumnNames(BaseModel):
    table_column_list: List[TableColumns]


class SQLGenerateResult(BaseModel):
    sql_statement: str
    status: Literal["OK", "ERROR", "IMPOSSIBLE"]
    reason: str 


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


class Execution2TableNames(BaseModel):
    """Model for execution error with table names."""
    user_query: str
    table_names: GetTableNames
    column_names: List[str]
    sql_statement: str
    error_description: str
