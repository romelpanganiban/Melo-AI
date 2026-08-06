from memory.memory_manager import MemoryManager


class ChatService:

    def __init__(self):
        self.memory = MemoryManager()

    def process_message(self, message):

        self.memory.add_message(
            "user",
            message
        )

        history = self.memory.get_history()

        last_messages = history[-5:]

        response = (
            f"Hello! I currently remember "
            f"{len(history)} messages in this conversation."
        )

        self.memory.add_message(
            "assistant",
            response
        )

        return {
            "response": response,
            "recent_history": last_messages
        }

    def get_history(self):
        return self.memory.get_history()