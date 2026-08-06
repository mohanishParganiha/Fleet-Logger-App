"""Custom exceptions for TripLog service."""
class TripLogServiceError(Exception):
    """Base exception for TripLog service errors."""
    pass

class TripNotFound(TripLogServiceError):
    """Raised when a trip log is not found."""
    pass

class TripAlreadyApproved(TripLogServiceError):
    """Raised when attempting to approve an already approved trip."""
    pass

class InvalidCalculationInput(TripLogServiceError):
    """Raised when calculation input validation fails."""
    pass