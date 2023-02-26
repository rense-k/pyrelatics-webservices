import os
import pathlib

# from setuptools import setup
import setuptools

long_description = ""  # pylint: disable=invalid-name
with open("README.md", "r", encoding="utf-8") as fh:
    long_description += fh.read()
long_description += "\n"
with open("CHANGELOG.md", "r", encoding="utf-8") as fh:
    long_description += fh.read()


# Retrieve the __version__ from the pyrelatics2/version.py file,
# in an other way than importing it (which doesn't work).
version_filename = os.path.join(os.path.realpath(os.path.dirname(__file__)), "pyrelatics2", "version.py")
version_content = pathlib.Path(version_filename).read_text("utf-8")
version_compiled = compile(version_content, version_filename, "exec")
exec(version_compiled)  # pylint: disable=exec-used


# LONG_DESCRIPTION = """
# Python package to interact with Relatics webservices.

# This package allows you to interact with Relatics webservices in two
# ways:

# * Get data from a "Servers for providing data" webservice.
# * Submit data to a "Servers for receiving data" webservice.

# Three authentication methods are supported: "_OAuth 2.0 - Client
# credentials_", "_Entry code_" and "_Unauthenticated_".
# """

setuptools.setup(
    name="pyrelatics2",
    version=__version__,  # pylint: disable=undefined-variable # type: ignore
    packages=[
        "pyrelatics2",
    ],
    install_requires=[
        "suds-community>=1.1.2",
        "colorama",
    ],
    extras_require={
        "development": ["black", "isort", "pylint", "wheel", "twine"],
    },
    license="Apache-2.0",
    url="https://github.com/rense-k/pyrelatics2",
    author="Rense Klinkenberg",
    author_email="r@klinkenberg.ws",
    description="Python package to interact with Relatics webservices",
    # long_description=LONG_DESCRIPTION,
    long_description=long_description,
    long_description_content_type="text/markdown",
    python_requires=">=3.10",
    # See PEP-301 for the classifier specification. For a complete
    # list of available classifiers see
    # 'http://pypi.python.org/pypi?%3Aaction=list_classifiers'.
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: Apache Software License",
        "Natural Language :: English",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3 :: Only",
        "Programming Language :: Python :: 3.10",
        "Topic :: Internet",
        "Topic :: Software Development :: Libraries",
    ],
    keywords=["Relatics", "webservice", "soap-client", "oauth2"],
    test_suite="tests",
    tests_require=["parameterized"],
)
