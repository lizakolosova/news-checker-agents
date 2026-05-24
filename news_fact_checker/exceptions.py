class ClaimExtractionError(Exception):
    pass


class InvalidConfigurationError(ClaimExtractionError):
    pass


class SentenceSegmentationError(ClaimExtractionError):
    pass


class ClaimClassificationError(ClaimExtractionError):
    pass


class VerifiabilityAssessmentError(ClaimExtractionError):
    pass


class EntityExtractionError(ClaimExtractionError):
    pass