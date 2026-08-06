class BaseAgent:

    def run(self, message):
        raise NotImplementedError(
            "Agent must implement run()"
        )