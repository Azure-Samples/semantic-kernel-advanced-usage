import logging
from typing import TYPE_CHECKING

from semantic_kernel.kernel import Kernel
from semantic_kernel.functions.kernel_arguments import KernelArguments
from semantic_kernel.functions.kernel_function import KernelFunction
from semantic_kernel.kernel_pydantic import KernelBaseModel
from semantic_kernel.contents.utils.author_role import AuthorRole

if TYPE_CHECKING:
    from semantic_kernel.contents.chat_message_content import ChatMessageContent

logger: logging.Logger = logging.getLogger(__name__)


class FeedbackStrategy(KernelBaseModel):
    """A strategy for determining when a Planned Team should terminate, and provide feedback to reiterate the plan if needed."""

    kernel: Kernel

    async def provide_feedback(
        self, history: list["ChatMessageContent"]
    ) -> tuple[bool, str]:
        raise NotImplementedError("should_terminate not implemented")


class FeedbackResponse(KernelBaseModel):
    should_terminate: bool
    feedback: str


class DefaultFeedbackStrategy(FeedbackStrategy):
    """A simple feedback strategy that always returns True and an empty string."""

    async def provide_feedback(
        self, history: list["ChatMessageContent"]
    ) -> tuple[bool, str]:
        return True, ""


class KernelFunctionFeedbackStrategy(FeedbackStrategy):
    """A strategy for determining when a Planned Team should terminate, and provide feedback to reiterate the plan if needed."""

    kernel: Kernel
    function: KernelFunction

    async def provide_feedback(
        self, history: list["ChatMessageContent"]
    ) -> tuple[bool, str]:
        """ """
        # Flatten the history
        messages = [
            {
                "role": str(message.role),
                "content": message.content,
                "name": message.name or "user",
            }
            for message in history
            if message.role in [AuthorRole.USER, AuthorRole.ASSISTANT]
        ]

        # Invoke the function
        arguments = KernelArguments()
        arguments["history"] = messages

        execution_settings = {}
        # https://devblogs.microsoft.com/semantic-kernel/using-json-schema-for-structured-output-in-python-for-openai-models/
        execution_settings["response_format"] = FeedbackResponse

        result = await self.function.invoke(
            kernel=self.kernel,
            arguments=arguments,
            execution_settings=execution_settings,
        )
        logger.info(f"FeedbackStrategy: {result}")
        parsed_result = FeedbackResponse.model_validate_json(result.value[0].content)

        return parsed_result.should_terminate, parsed_result.feedback
