import sys
import os
# Load environment variables
from dotenv import load_dotenv
load_dotenv()

sys.path.append("../../")
from semantic_kernel.contents import ChatHistory
from semantic_kernel.connectors.ai.chat_completion_client_base import ChatCompletionClientBase
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion
from semantic_kernel.kernel import Kernel

SERVICE_ID = "default"
REASONING_EFFORT = os.environ.get("REASONING_EFFORT", "medium")


async def initialize_kernel() -> Kernel:
    """Initialize the kernel with the chat completion service."""
    kernel = Kernel()
    chat_service = AzureChatCompletion(service_id=SERVICE_ID)
    kernel.add_service(chat_service)
    print("AzureChatCompletion service registered with kernel.")
    return kernel

async def call_chat_completion(kernel, user_query: str, reasoning_effort=REASONING_EFFORT) -> str:
    """
    Call the chat completion service and return the response as a string.
    
    Args:
        kernel: The Semantic Kernel instance
        user_query: The query to send to the chat completion service
        
    Returns:
        String response from the chat completion service
    """
    # Get chat completion service and generate response
    chat_service: ChatCompletionClientBase = kernel.get_service(service_id=SERVICE_ID)
    settings = chat_service.instantiate_prompt_execution_settings(service_id=SERVICE_ID)

    print(f"Model used: {os.environ['AZURE_OPENAI_CHAT_DEPLOYMENT_NAME']}")
    if (os.environ['AZURE_OPENAI_CHAT_DEPLOYMENT_NAME'] == "o1") or \
       (os.environ['AZURE_OPENAI_CHAT_DEPLOYMENT_NAME'] == "o3-mini"):
        settings.reasoning_effort = reasoning_effort
        print("Using reasoning effort:", settings.reasoning_effort)

    chat_history = ChatHistory()
    chat_history.add_user_message(user_query)
    response = await chat_service.get_chat_message_contents(chat_history=chat_history, settings=settings)

    if response is None:
        raise ValueError("Failed to get a response from the chat completion service.")

    answer = response[0].content
    return answer

async def call_chat_completion_structured_outputs(kernel, user_query: str, response_format: any, reasoning_effort=REASONING_EFFORT) -> any:
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
    chat_service: ChatCompletionClientBase = kernel.get_service(service_id=SERVICE_ID)
    settings = chat_service.instantiate_prompt_execution_settings(service_id=SERVICE_ID)
    settings.response_format = response_format

    print(f"Model used: {os.environ['AZURE_OPENAI_CHAT_DEPLOYMENT_NAME']}")
    if (os.environ['AZURE_OPENAI_CHAT_DEPLOYMENT_NAME'] == "o1") or \
       (os.environ['AZURE_OPENAI_CHAT_DEPLOYMENT_NAME'] == "o3-mini"):
        settings.reasoning_effort = reasoning_effort
        print("Using reasoning effort:", settings.reasoning_effort)

    chat_history = ChatHistory()
    chat_history.add_user_message(user_query)
    response = await chat_service.get_chat_message_contents(chat_history=chat_history, settings=settings)

    if response is None:
        raise ValueError("Failed to get a response from the chat completion service.")

    answer = response[0].content
    # Parse the JSON response into the specified Pydantic model
    answer = response_format.model_validate_json(answer)
    return answer
