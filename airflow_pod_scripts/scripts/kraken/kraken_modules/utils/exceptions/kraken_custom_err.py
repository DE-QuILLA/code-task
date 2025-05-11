class KrakenBaseError(Exception):
    def __init__(self, message):
        super().__init__(message)

class KrakenRestApiErrorInResponseError(KrakenBaseError):
    pass

class KrakenRestApiNoDataError(KrakenBaseError):
    pass

class KrakenRestApiJsonLoadsError(KrakenBaseError):
    pass

class KrakenRestApiJsonDumpsError(KrakenBaseError):
    pass
