class MeloAIException(Exception):
    pass


class SessionNotFoundError(
    MeloAIException
):
    pass


class SettingsError(
    MeloAIException
):
    pass