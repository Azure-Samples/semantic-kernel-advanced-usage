import sys
import os
import json
from semantic_kernel.contents import ChatHistory
# Load environment variables
from dotenv import load_dotenv
load_dotenv()

sys.path.append("../../")
# Imports for Semantic Kernel
from semantic_kernel import Kernel
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion
from semantic_kernel.connectors.ai.open_ai.prompt_execution_settings.open_ai_prompt_execution_settings import OpenAIPromptExecutionSettings

SERVICE_ID = "default"
REASONING_EFFORT = "low"

async def initialize_kernel():
    """Initialize the kernel with the chat completion service."""
    kernel = Kernel()
    chat_service = AzureChatCompletion(
        deployment_name=os.environ["AZURE_OPENAI_CHAT_DEPLOYMENT_NAME"],
        endpoint=os.environ["AZURE_OPENAI_ENDPOINT"],
        api_key=os.environ["AZURE_OPENAI_API_KEY"],
        service_id=SERVICE_ID
    )
    kernel.add_service(chat_service)
    print("AzureChatCompletion service registered with kernel.")
    return kernel

async def call_chat_completion(kernel, user_query: str) -> str:
    """
    Call the chat completion service and return the response as a string.
    
    Args:
        kernel: The Semantic Kernel instance
        user_query: The query to send to the chat completion service
        
    Returns:
        String response from the chat completion service
    """
    # Get chat completion service and generate response
    chat_service = kernel.get_service(SERVICE_ID)
    
    print(f"Model used: {os.environ['AZURE_OPENAI_CHAT_DEPLOYMENT_NAME']}")
    
    # Create a ChatHistory object and add the user's message
    chat_history = ChatHistory()
    chat_history.add_user_message(user_query)
    
    # Create proper settings object for SK 1.28.0
    settings = OpenAIPromptExecutionSettings()
    
    # Use the correct chat completion method for SK 1.28.0
    response = await chat_service.get_chat_message_content(chat_history, settings)

    if response is None:
        raise ValueError("Failed to get a response from the chat completion service.")

    return response.content

async def call_chat_completion_structured_outputs(kernel, user_query: str, response_format: any) -> any:
    """
    Call the chat completion service and return the response as a structured output.
    
    Args:
        kernel: The Semantic Kernel instance
        user_query: The query to send to the chat completion service
        response_format: The Pydantic model to use for parsing the response
        
    Returns:
        Structured output in the format specified by response_format
    """
    # Get chat completion service and generate response
    chat_service = kernel.get_service(SERVICE_ID)
    
    # Create a ChatHistory object and add the user's message
    chat_history = ChatHistory()
    chat_history.add_user_message(user_query)
    
    # Create proper settings object for SK 1.28.0 with JSON response format
    settings = OpenAIPromptExecutionSettings(response_format={"type": "json_object"})
    
    print(f"Model used: {os.environ['AZURE_OPENAI_CHAT_DEPLOYMENT_NAME']}")
    
    # Use the correct chat completion method for SK 1.28.0
    response = await chat_service.get_chat_message_content(chat_history, settings)

    if response is None:
        raise ValueError("Failed to get a response from the chat completion service.")

    # Parse the JSON response into the specified Pydantic model
    try:
        answer_text = response.content
        answer_dict = json.loads(answer_text)
        return response_format.model_validate(answer_dict)
    except Exception as e:
        print(f"Error parsing response: {e}")
        print(f"Response was: {response.content}")
        raise ValueError(f"Failed to parse response into structured output: {e}")
