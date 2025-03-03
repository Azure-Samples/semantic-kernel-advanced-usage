import sys
sys.path.append("../../")

from enum import Enum, auto


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
    
    # Validation events
    ValidationPassed = "ValidationPassed"
    ValidationFailed = "ValidationFailed"
    
    # Execution events
    ExecutionSuccess = "ExecutionSuccess"
    ExecutionError = "ExecutionError"
