class XNativeError(Exception):
    """Base project exception."""


class CaptureError(XNativeError):
    pass


class ValidationError(XNativeError):
    pass


class ModelUnavailable(XNativeError):
    pass


class RetryableJobError(XNativeError):
    pass


class FatalJobError(XNativeError):
    pass


class StageTimeoutError(RetryableJobError):
    pass
