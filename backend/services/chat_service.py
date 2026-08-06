from memory.memory_manager import MemoryManager
from core.logger import logger


class ChatService:

    def __init__(self):
        self.memory = MemoryManager()

    def process_message(
        self,
        session_id,
        message
    ):

        logger.info(
            f"Message received: {message}"
        )

        self.memory.add_message(
            session_id,
            "user",
            message
        )

        history = self.memory.get_session_history(
            session_id
        )

        response = (
            f"Hello! I currently remember "
            f"{len(history)} messages in this session."
        )

        self.memory.add_message(
            session_id,
            "assistant",
            response
        )

        logger.info(
            "Response generated"
        )

        return {
            "response": response,
            "recent_history": history[-5:]
        }

    def get_history(
        self,
        session_id
    ):
        return self.memory.get_session_history(
            session_id
        )