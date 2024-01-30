from logging import getLogger
from pprint import pformat

log = getLogger(__name__)


class TokenRequestError(Exception):
    """
    Custom exception class when the server returns an error while retrieving the OAuth2 token

    Attributes:
        error : The error string received from the server
        error_description : The error description string received from the server
        response_json : Dictionary with the json parsed response
    """

    def __init__(self, response_dict: dict, *args):
        super().__init__(*args)
        self.error = response_dict["error"]
        self.error_description = response_dict["error_description"]
        self.response_dict = response_dict

        log.debug(
            "Token request failed: %s (%s) | %s",
            self.error,
            self.error_description,
            pformat(self.response_dict, indent=2),
        )

    def __str__(self) -> str:
        return f"Token request failed: {self.error} ({self.error_description})"
