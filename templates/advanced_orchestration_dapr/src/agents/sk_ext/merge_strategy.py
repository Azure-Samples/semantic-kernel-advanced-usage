import logging

from semantic_kernel.kernel import Kernel
from semantic_kernel.functions.kernel_arguments import KernelArguments
from semantic_kernel.functions.kernel_function import KernelFunction
from semantic_kernel.kernel_pydantic import KernelBaseModel
from semantic_kernel.contents.chat_message_content import ChatMessageContent
from semantic_kernel.contents.utils.author_role import AuthorRole

logger: logging.Logger = logging.getLogger(__name__)


class MergeHistoryStrategy(KernelBaseModel):
    """A strategy for determining when a Planned Team should terminate, and provide feedback to reiterate the plan if needed."""

    kernel: Kernel

    async def merge(
        self,
        original_history: list["ChatMessageContent"],
        new_history: list["ChatMessageContent"],
    ) -> list["ChatMessageContent"]:
        raise NotImplementedError("merge not implemented")


class LastMessageMergeHistoryStrategy(MergeHistoryStrategy):
    """A strategy that merges the last message from the original history with the new history."""

    async def merge(
        self,
        original_history: list["ChatMessageContent"],
        new_history: list["ChatMessageContent"],
    ) -> list["ChatMessageContent"]:
        delta = [new_history[-1]]
        original_history.extend(delta)

        return delta


class KernelFunctionMergeHistoryStrategy(MergeHistoryStrategy):
    """A strategy that merges the last message from the original history with the new history."""

    kernel_function: KernelFunction

    async def merge(
        self,
        original_history: list["ChatMessageContent"],
        new_history: list["ChatMessageContent"],
    ) -> list["ChatMessageContent"]:
        messages = new_history[len(original_history) :]
        arguments = KernelArguments()
        arguments["messages"] = "\n".join(
            [
                f"""
- {m.name} ({str(m.role)})
    {m.content}
        
            """
                for m in messages
                if m.role in [AuthorRole.USER, AuthorRole.ASSISTANT]
            ]
        )
        logger.debug(
            "KernelFunctionMergeHistoryStrategy: Invoking kernel function with arguments: %s",
            arguments,
        )
        result = await self.kernel_function.invoke(self.kernel, arguments=arguments)
        logger.debug("KernelFunctionMergeHistoryStrategy: Received result: %s", result)
        merged_message = ChatMessageContent(
            role=AuthorRole.ASSISTANT, content=result.value[0].content
        )
        original_history.append(merged_message)
        logger.debug(
            "KernelFunctionMergeHistoryStrategy: Appended merged message: %s",
            merged_message,
        )

        return [merged_message]
