import sys

if sys.version < "3.11":
    from typing_extensions import Self  # pragma: no cover
else:
    from typing import Self  # type: ignore # pragma: no cover
from semantic_kernel.contents.utils.author_role import AuthorRole
from semantic_kernel.contents.history_reducer import ChatHistoryReducer


class ContextAwareChatHistoryReducer(ChatHistoryReducer):

    async def reduce(self) -> Self | None:
        # Keep a system message (if any) at the beginning of the messages
        system_messages = []
        for message in self.messages:
            if message.role == AuthorRole.SYSTEM:
                system_messages.append(message)
                continue

        # Only the last few messages are kept
        messages_to_keep = system_messages + self.messages[-self.max_tokens:]

        if len(messages_to_keep) >= len(self.messages):
            # No need to reduce
            return None

        # Replace the messages with the reduced set
        self.messages = messages_to_keep
        return self
