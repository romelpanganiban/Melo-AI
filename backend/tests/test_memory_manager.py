from memory.memory_manager import MemoryManager


def test_add_message():

    manager = MemoryManager()

    manager.add_message(
        "test-session",
        "user",
        "Hello"
    )

    history = manager.get_history()

    assert len(history) > 0