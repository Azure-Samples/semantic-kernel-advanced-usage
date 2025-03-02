import sys

if sys.version < "3.11":
    from typing_extensions import Self  # pragma: no cover
else:
    from typing import Self  # type: ignore # pragma: no cover
from semantic_kernel.contents.history_reducer.chat_history_reducer import (
    ChatHistoryReducer,
)


class VisualizationChatHistoryReducer(ChatHistoryReducer):

    async def reduce(self) -> Self | None:
        # Remove all messages with content that contains "PAUSR"
        # and script all text after "~~~context~~~" marker
        messages_to_keep = []
        for message in self.messages:
            if "PAUSE" in message.content:
                continue
            if "~~~context~~~" in message.content:
                message.content = message.content.split("~~~context~~~")[0]
            messages_to_keep.append(message)
        self.messages = messages_to_keep
        return self
