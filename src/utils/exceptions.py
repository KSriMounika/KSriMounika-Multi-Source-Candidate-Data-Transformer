class TransformerBaseException(Exception):
    """Base exception for all candidate transformer errors."""
    pass

class ExtractionError(TransformerBaseException):
    """Raised when a file cannot be read or parsed."""
    pass

class ValidationError(TransformerBaseException):
    """Raised when the final output does not match the requested schema."""
    pass
