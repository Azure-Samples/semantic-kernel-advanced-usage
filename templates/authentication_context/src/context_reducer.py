import sys

if sys.version < "3.11":
    from typing_extensions import Self  # pragma: no cover
else:
    from typing import Self  # type: ignore # pragma: no cover
from semantic_kernel.contents.chat_message_content import ChatMessageContent
from semantic_kernel.contents.utils.author_role import AuthorRole
from semantic_kernel.contents.history_reducer.chat_history_reducer import (
    ChatHistoryReducer,
)


class ContextAwareChatHistoryReducer(ChatHistoryReducer):

    async def reduce(self) -> Self | None:
        # Process messages: aggregate key-value pairs from lines of messages
        # containing "~~~context~~~", and filter them out from the history.
        context = {}
        messages_to_keep = []
        for message in self.messages:
            if "~~~context~~~" in message.content:
                # Process each line that doesn't contain the marker.
                for line in message.content.splitlines():
                    if "~~~context~~~" in line:
                        continue
                    if ":" in line:
                        key, value = line.split(":", 1)
                        key = key.strip()
                        value = value.strip()
                        if key:
                            context[key] = value
            else:
                messages_to_keep.append(message)

        if context:
            context_message = ChatMessageContent()
            context_message.role = (
                AuthorRole.ASSISTANT
            )  # TODO check is SYSTEM makes more sense
            context_message.name = "context-provider"
            # Build the context message content by joining key-value lines.
            context_lines = [f"{key}={value}" for key, value in context.items()]
            context_message.content = "Conversation context:\n" + "\n".join(
                context_lines
            )
            # Insert the context message at the beginning.
            self.messages = [context_message] + messages_to_keep
        else:
            self.messages = messages_to_keep

        return self
