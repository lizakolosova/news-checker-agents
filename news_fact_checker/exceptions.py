"""Custom exceptions for the claim extraction system."""


class ClaimExtractionError(Exception):
    """Base exception for claim extraction errors."""
    pass


class InvalidConfigurationError(ClaimExtractionError):
    """Raised when configuration is invalid."""
    pass


class SentenceSegmentationError(ClaimExtractionError):
    """Raised when sentence segmentation fails."""
    pass


class ClaimClassificationError(ClaimExtractionError):
    """Raised when claim classification fails."""
    pass


class VerifiabilityAssessmentError(ClaimExtractionError):
    """Raised when verifiability assessment fails."""
    pass


class EntityExtractionError(ClaimExtractionError):
    """Raised when entity extraction fails."""
    pass