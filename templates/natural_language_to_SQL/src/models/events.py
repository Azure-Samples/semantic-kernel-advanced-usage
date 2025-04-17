import sys
sys.path.append("../../")

from enum import Enum


class SQLEvents(str, Enum):
    """Events used by the SQL generation process."""
    
    # Process control events
    StartProcess = "StartProcess"
    ErrorOccurred = "ErrorOccurred"
    
    # Step completion events
    TableNameStepDone = "TableNameStepDone"
    ColumnNameStepDone = "ColumnNameStepDone"
    SQLGenerationStepDone = "SQLGenerationStepDone"
    SQLGenerationStepFailed = "SQLGenerationStepFailed"
    BusinessRulesStepDone = "BusinessRulesStepDone"
    BusinessRulesFailed = "BusinessRulesFailed"
      # Execution events
    ExecutionSuccess = "ExecutionSuccess"
    ExecutionError = "ExecutionError"
    RetryWithAzureSQLSyntax = "RetryWithAzureSQLSyntax"
    
    # Validation events
    ValidationPassed = "ValidationPassed"
    ValidationFailed = "ValidationFailed"
