import os
import platform
import sys

PACKAGE_VERSION = "0.2.0"

TOKEN_PATH = "/oauth2/token"
IMPORT_BASENAME = "pyrelatics_webservice"
SUPPORTED_EXTENSIONS = ["xlsx", "xlsm", "xlsb", "xls", "csv"]

USER_AGENT = (
    f"PyRelatics2/{PACKAGE_VERSION} "
    f"({platform.platform()}; {platform.machine()}; python-{platform.python_version()}) "
    f"{os.path.split(sys.modules['__main__'].__file__)[1]}"  # pylint: disable=E1101
)
