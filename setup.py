from setuptools import setup

# with open("README.md", "r") as fh:
#     long_description = fh.read()

LONG_DESCRIPTION = """
Python package to interact with Relatics webservices.

This package allows you to interact with Relatics webservices in two
ways:

* Get data from a "Servers for providing data" webservice.
* Submit data to a "Servers for receiving data" webservice.

Three authentication methods are supported: "_OAuth 2.0 - Client
credentials_", "_Entry code_" and "_Unauthenticated_".
"""

setup(
    name="pyrelatics2",
    version="0.1.1",
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
    long_description=LONG_DESCRIPTION,
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
    ],
    keywords=["Relatics", "webservice", "soap-client", "oauth2"],
    # test_suite="nose.collector",
    # tests_require=["nose"],
)
