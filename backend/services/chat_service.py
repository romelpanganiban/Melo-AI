from memory.memory_manager import MemoryManager


class ChatService:

    def __init__(self):
        self.memory = MemoryManager()

    def process_message(self, message):

        self.memory.add_message(
            "user",
            message
        )

        response = (
            f"Melo-AI received: {message}"
        )

        self.memory.add_message(
            "assistant",
            response
        )

        return response