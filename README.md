# PyRelatics2

[![PyPI Python version][pypi-python-version-badge]][pypi-package] [![PyPI version][pypi-version-badge]][pypi-package] [![PyPI status][pypi-status-badge]][pypi-package] [![Apache-2.0 license][license-badge]][license] [![GitHub branch check state][github-workflow-status-pylint-badge]][github-link]

Python package to interact with Relatics webservices.

This package allows you to interact with Relatics webservices in two ways:

* Get data from a "Servers for providing data" webservice.
* Submit data to a "Servers for receiving data" webservice.

Three authentication methods are supported: "_OAuth 2.0 - Client credentials_", "_Entry code_" and "_Unauthenticated_".

## Setting up

```python
from pyrelatics2 import RelaticsWebservices

client = RelaticsWebservices("company_subdomain", "workspace_id")
```

When using "OAuth 2.0 - Client credentials", the client credentials can be stored in a dedicated class instance for
later use.

```python
from pyrelatics2 import ClientCredential

cc = ClientCredential(client_id="client_id", client_secret="client_secret")
```

## Example of getting data

Getting data with "OAuth 2.0 - Client credentials":

```python
from pyrelatics2 import ClientCredential, RelaticsWebservices

cc = ClientCredential(client_id="client_id", client_secret="client_secret")
client = RelaticsWebservices("company_subdomain", "workspace_id")

# Optionally prepare a dictionary of parameters
parameters = {
    "sample_parameter_name_1": "sample_parameter_value_1",
    "sample_parameter_name_2": "sample_parameter_value_2",
}

client.get_result(operation_name="sample_operation", parameters=parameters, authentication=cc)
```

Other forms of authentication can also be used:

```python
from pyrelatics2 import RelaticsWebservices

client = RelaticsWebservices("company_subdomain", "workspace_id")

# Authentication via entry code
entry_code = "sample_entry_code"
client.get_result(operation_name="sample_operation", parameters=None, authentication=entry_code)

# No authentication
client.get_result(operation_name="sample_operation", parameters=None, authentication=None)
```

## Example of sending data

Sending data with "OAuth 2.0 - Client credentials", with data as `list`:

```python
from pyrelatics2 import ClientCredential, RelaticsWebservices

cc = ClientCredential(client_id="client_id", client_secret="client_secret")
client = RelaticsWebservices("company_subdomain", "workspace_id")

# Prepare the data to be send
data = [
    {"name": "test name 1", "description": "test description 1"},
    {"name": "test name 2", "description": "test description 2"},
]

client.run_import(operation_name="sample_operation", data=data, authentication=cc)
```

Again, other forms of authentication can also be used:

```python
from pyrelatics2 import RelaticsWebservices

client = RelaticsWebservices("company_subdomain", "workspace_id")
data = [{"name": "test 1", "description": "desc 1"},{"name": "test 2", "description": "desc 2"}]

# Authentication via entry code
entry_code = "sample_entry_code"
client.run_import(operation_name="sample_operation", data=data, authentication=entry_code)

# No authentication
client.run_import(operation_name="sample_operation", data=data, authentication=None)
```

## Example of sending data and documents

It is possible to include documents as part of the upload, as described in [Use import for uploading files](https://kb.relaticsonline.com/published//ShowObject.aspx?Key=7126fb9d-58df-e311-9406-00155de0940e). Simply add list of the
filepaths to be included.

```python
from pyrelatics2 import ClientCredential, RelaticsWebservices

cc = ClientCredential(client_id="client_id", client_secret="client_secret")
client = RelaticsWebservices("company_subdomain", "workspace_id")

# Prepare the data and documents to be send
data = [
    {"name": "test name 1", "description": "test description 1", "reference": "file_a.jpg"},
    {"name": "test name 2", "description": "test description 2", "reference": "file_b.jpg"},
]
documents=[
    "sample-data\\file_a.jpg",
    "sample-data\\file_b.jpg",
]

client.run_import(operation_name="sample_operation", data=data, authentication=cc, documents=documents)
```

## Example of sending data from a file

Instead of supplying the data with a list, it is possible to give the filepath of a supported file type. Supported
file type are defined in [Supported file types for import](https://kb.relaticsonline.com/published//ShowObject.aspx?Key=c57bfd5e-20df-e311-9406-00155de0940e)
as "MS Excel, XML and comma-separated ASCII". The code will except these file extensions: `xlsx`, `xlsm`, `xlsb`,
`xls` or `csv`.

```python
from pyrelatics2 import ClientCredential, RelaticsWebservices

cc = ClientCredential(client_id="client_id", client_secret="client_secret")
client = RelaticsWebservices("company_subdomain", "workspace_id")

# Prepare the data and documents to be send
data = "sample-data\\sample_data.xlsx"

client.run_import(operation_name="sample_operation", data=data, authentication=cc)
```

## Result of `get_result()`

* When the report does not include ReferenceFile attributes, `get_result()` will return a `suds.sudsobject.Object`.
* When the report does include a ReferenceFile attribute, `get_result()` will return a `tuple`. The first entry will
  be the `suds.sudsobject.Object`. The second entry will be `dict`, where the keys are the filenames and the values
  are the contents of the file. [^1]

## Result of `run_import()`

The raw response of an import will be processed into a `ImportResult` object. When an error was registered, it will
become Falsly for easy checking. The `ImportResult` object will contain all the messages, including properties to
easily retrieve them by their status (`Progress`, `Comment`, `Success`, `Warning`, `Error`).

The `ImportResult` object also includes all the updated that Relatics made to instances. They contain their ID and
possible ForeignKey. Properties are available to easily retrieve them by their action (`Add`, `Update`).

When the `ImportResult` object is `print()`, it will display a formatted and human presentable outcome of the import
process. [^2]

## Exceptions

In addition to basic Exceptions, there are some custom exceptions the code will raise:

* `TokenRequestError`: When the token for a "OAuth 2.0 - Client credentials" authentication could not be retrieved.
* `InvalidWorkspaceError`: When Relatics responses that the given `workspace_id` is not valid.
* `InvalidOperationError`: When Relatics indicates that the given `operation_name` does not exists in the given
  `workspace_id`.

## Logging

This package uses the standard Python `logging` functionality. Logging can be activated with:

```python
import logging

LOG_FORMAT = "%(asctime)s %(name)s %(levelname)s %(message)s"  # Define a custom log format
logging.basicConfig(level=logging.INFO, format=LOG_FORMAT)

logging.getLogger("pyrelatics2.client").setLevel(logging.DEBUG)
```

Logging is available in these modules for debugging purpose: `pyrelatics2.client`, `pyrelatics2.exceptions` and
`pyrelatics2.import_result_classes`.

[^1]: The handling of the ReferenceFiles can be turned off via the `auto_handle_documents=false` argument. In that case
      the raw base64 encoded zip containing the documents will be part of the `suds.sudsobject.Object`.
[^2]: Parsing of the raw response can be turned off via the `auto_parse_response=false` argument. In that case the
      method will return the raw response in the form of a `suds.sudsobject.Object`

[pypi-package]: https://pypi.org/project/pyrelatics2/
[pypi-version-badge]: https://img.shields.io/pypi/v/pyrelatics2?label=pypi%20package
[pypi-status-badge]: https://img.shields.io/pypi/status/pyrelatics2
[pypi-python-version-badge]: https://img.shields.io/pypi/pyversions/pyrelatics2
[github-link]: https://github.com/rense-k/pyrelatics2
[github-workflow-status-pylint-badge]: https://img.shields.io/github/actions/workflow/status/rense-k/pyrelatics2/pylint.yml?label=pylint
[license]: ./LICENSE
[license-badge]: https://img.shields.io/pypi/l/pyrelatics2?color=informational
