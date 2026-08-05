class LoadTestError(Exception):
    """Classe de base pour toutes les erreurs métier du load test."""


class DatasetUploadError(LoadTestError):
    """Raised when a dataset upload fails."""


class DatasetCreateError(LoadTestError):
    """Raised when a dataset creation fails."""


class DatasetCompletionError(LoadTestError):
    """Raised when a dataset completion fails."""


class SubmissionCreationError(LoadTestError):
    """Raised when a submission creation fails."""


class SubmissionStatusError(LoadTestError):
    """Raised when a submission status check fails."""


class SubmissionCancellationError(LoadTestError):
    """Raised when a submission cancellation fails."""
