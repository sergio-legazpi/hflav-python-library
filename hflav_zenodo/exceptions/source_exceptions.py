class SourceException(Exception):
    """Base exception for source-related errors"""

    pass


class DataAccessException(SourceException):
    """Error accessing data source"""

    def __init__(self, message="Error accessing data source", details=None):
        self.message = message
        self.details = details
        super().__init__(self.message)


class DataNotFoundException(SourceException):
    """Error when data is not found"""

    def __init__(self, message="No data found", details=None):
        self.message = message
        self.details = details
        super().__init__(self.message)


class NoSchemaFoundInsideGitlabRepository(SourceException):
    """Error when no schema is found inside the GitLab repository"""

    def __init__(
        self, message="No schema found inside the GitLab repository", details=None
    ):
        self.message = message
        self.details = details
        super().__init__(self.message)


class NoVersionTagFound(SourceException):
    """Error when no version tag is found inside the GitLab repository"""

    def __init__(
        self, message="No version tag found inside the GitLab repository", details=None
    ):
        self.message = message
        self.details = details
        super().__init__(self.message)
