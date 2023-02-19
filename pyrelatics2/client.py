import base64
import datetime
import http.client
import io
import json
import logging
import os
import pprint
import tempfile
import uuid
import zipfile

from suds.client import Client
from suds.plugin import MessagePlugin
from suds.sax.document import Document
from suds.sax.element import Element
from suds.sax.text import Text
from suds.sudsobject import Object as SudsObject

from .exceptions import InvalidOperationError, InvalidWorkspaceError, TokenRequestError
from .import_result_classes import ImportResult

log = logging.getLogger(__name__)

# Type aliases
ParametersOrNone = None | dict[str, str]

# Constants
TOKEN_PATH = "/oauth2/token"
USER_AGENT = "Python-pyrelatics_webservice/0.0.0"
IMPORT_BASENAME = "pyrelatics_webservice"
SUPPORTED_EXTENSIONS = ["xlsx", "xlsm", "xlsb", "xls", "csv"]


class ClientCredential:
    """
    Class containing OAuth2 client credentials and helper methods to get a token from the Relatics host.

    Args:
        client_id : The OAuth2 client_id
        client_secret : The OAuth2 client_secret
    """

    def __init__(self, client_id: str, client_secret: str):
        self.client_id = client_id
        self.client_secret = client_secret
        self.tokens: dict(str, dict(str, str)) = {}

        # self.tokens[hostname] = {
        #     "token": "string with the actual token",
        #     "expires_on": datetime object with the expire time,
        # }

    def get_token(self, hostname: str, force_refresh: bool = False, user_agent: str = USER_AGENT) -> str:
        """
        Get the token for the given hostname

        Args:
            hostname : The Relatics hostname from where the token should be get.
            force_refresh : When True, force a new token to be requested, instead of trying to reuse an
                            existing token. Defaults to False.
            user_agent : The user-agent used in the http request to Relatics. Since this name will show up in the
                         logs in Relatics, it can be useful to specify a custom value. Defaults to USER_AGENT.

        Returns:
            str: Token for the given hostname
        """
        if (
            force_refresh is True
            or hostname not in self.tokens
            or (self.tokens[hostname]["expires_on"] - datetime.datetime.now()).seconds <= 300
        ):
            log.info("No previous token for %s, retrieving new token", hostname)
            self.retrieve_token(hostname, user_agent)
        else:
            log.info("Reuse previous token for %s", hostname)

        return self.tokens[hostname]["token"]

    def retrieve_token(self, hostname: str, user_agent: str = USER_AGENT) -> None:
        """_summary_

        Args:
            hostname : The Relatics hostname from where the token should be get.
            user_agent : The user-agent used in the http request to Relatics. Since this name will show up in the
                         logs in Relatics, it can be useful to specify a custom value. Defaults to USER_AGENT.

        Raises:
            RuntimeError: When Relatics sends back an error response
            KeyError: When there is no token in the response from Relatics
        """
        requested_on = datetime.datetime.now()
        auth_credentials = base64.b64encode(bytes(f"{self.client_id}:{self.client_secret}", "utf-8"))
        payload = "grant_type=client_credentials"
        headers = {
            "Authorization": f"Basic {auth_credentials.decode('utf-8')}",
            "Content-Type": "text/plain",
            "User-Agent": user_agent,
        }

        conn = http.client.HTTPSConnection(hostname)
        conn.request("POST", TOKEN_PATH, payload, headers)
        res = conn.getresponse()
        data = res.read()
        response = json.loads(data.decode("utf-8"))

        log.debug("Response from %s: %s", TOKEN_PATH, pprint.pformat(response, indent=2))

        if "error" in response:
            # Known errors:
            # * `invalid_client` (description=_"Client not found."_). Happens when:
            #   * An unknown client_id is submitted
            #   * An incorrect client_secret is submitted
            #   * The client_id is disabled in Relatics
            raise TokenRequestError(response)

        if "access_token" not in response:
            raise KeyError("Token request failed: No access_token was given.")

        # Store the token for later use
        self.tokens[hostname] = {
            "token": response["access_token"],
            "expires_on": requested_on + datetime.timedelta(seconds=response["expires_in"]),
        }


class AddParametersPlugin(MessagePlugin):  # pylint: disable=R0903
    """
    Plugin for Suds Client to add parameters to the request before sending to Relatics. Because parameters use
    attributes, they can not be defined though the default mechanisms within Suds.

    Args:
        parameters : Dictionary with the parameters
    """

    def __init__(self, parameters: ParametersOrNone):
        self.parameters = parameters

    def marshalled(self, context):
        if self.parameters is not None:
            # Try to get "Parameters" element, or built when missing
            try:
                params = context.envelope.getChild("Body")[0].getChild("Parameters")[0]
            except TypeError:
                log.info("Adding parameters to SOAP request")
                root = context.envelope.getChild("Body")[0]
                root_prefix = root.findPrefix("http://www.relatics.com/")

                p_1 = Element("Parameters", parent=root)
                p_1.setPrefix(root_prefix)
                root.append(p_1)

                p_2 = Element("Parameters", parent=p_1)
                p_2.setPrefix(root_prefix)
                p_1.append(p_2)

                params = context.envelope.getChild("Body")[0].getChild("Parameters")[0]

            prefix = params.findPrefix("http://www.relatics.com/")

            # Add the parameters
            for param_name, param_value in self.parameters.items():
                elem = Element("Parameter", parent=params)
                elem.setPrefix(prefix)
                elem.set(name="Name", value=param_name)
                elem.set(name="Value", value=param_value)
                params.append(elem)

        log.debug("Final SOAP envelope: \n%s", context.envelope.str())


class RelaticsWebservices:
    """
    Class to communicate with Relatics webservices

    Args:
        company_subdomain : The company's subdomain (before ".relaticsonline.com")
        workspace_id : The ID of the Relatics workspace were the request will be send to
        user_agent : The user agent sent as part of the request. Will show up in the webservice-log in Relatics. Can
                     be used to distinguished different applications.

    """

    def __init__(self, company_subdomain: str, workspace_id: str, user_agent: str = USER_AGENT):
        self.hostname = f"{company_subdomain.lower()}.relaticsonline.com"
        self.wsdl_url = f"https://{self.hostname}/DataExchange.asmx?wsdl"
        self.workspace_id = workspace_id
        self.identification = {"Identification": {"Workspace": workspace_id}}
        self.user_agent = user_agent
        self.keep_zip_file = False  # Optionally keep the created zipfile. For debugging purpose only

        # Check of mandatory arguments are given
        if company_subdomain == "":
            raise ValueError("The 'company_subdomain' can not be empty.")
        if workspace_id == "":
            raise ValueError("The 'workspace_id' can not be empty.")

        # Check if workspace_id is a version ## GUID
        id_is_uuid: bool = True
        try:
            uuid.UUID(workspace_id)
        except ValueError:
            id_is_uuid = False

        if id_is_uuid is False:
            log.warning(
                "The supplied workspace ID isn't a GUID. Make sure the workspace has an overridden 'URL' in Relatics."
            )

    @staticmethod
    def _handle_response_errors(suds_response) -> None:
        """Raise Exceptions for known errors"""
        if suds_response is not None and hasattr(suds_response, "Export") and hasattr(suds_response.Export, "_Error"):
            error_msg = suds_response.Export._Error  # pylint: disable=W0212
            log.info("Received an error response from the request: %s", error_msg)

            if error_msg in {"Invalid import webservice", "Invalid receiving webservice"}:
                raise InvalidOperationError(error_msg)
            if "No active workspace found for the given identifier." == error_msg:
                raise InvalidWorkspaceError(error_msg)

    @staticmethod
    def _check_operation_name(operation_name: str) -> None:
        if operation_name == "":
            raise ValueError("Supplied operationName is empty.")

    @staticmethod
    def _generate_auth_parameter(authentication: None | str | ClientCredential = None) -> dict:
        if isinstance(authentication, str):
            auth = {"Authentication": {"Entrycode": authentication}}
        else:
            auth = {"Authentication": {}}  # Default value, because Relatics doesn't like this to be empty

        return auth

    def get_result(
        self,
        operation_name: str,
        parameters: ParametersOrNone = None,
        authentication: None | str | ClientCredential = None,
        auto_handle_documents: bool = True,
    ) -> SudsObject | tuple[SudsObject, dict[str, bytes]]:
        """
        Retrieve results from a "Server for providing data" in Relatics, without checking any results

        Args:
            operation_name : The "OperationName" of the webservice to call
            parameters : The parameters to pass to the webservice
            authentication : Authentication for the webservice, either:
                             * None for no authentication,
                             * str for entryCode authentication or
                             * ClientCredential for OAuth2 client credentials
            auto_handle_documents : When the result contains a document node, convert them to a dict for easy access

        Raises:
            InvalidOperationError: When an invalid operation_name is supplied
            InvalidWorkspaceError: When an invalid workspace_id is supplied

        Returns:
            suds.sudsobject.Object : The retrieved data, when there were no documents that were handled
            tuple[suds.sudsobject.Object, dict[str, bytes]] : When document were retrieved  and handled. The first part
                                                              of the tuple contains the retrieved data. The second part
                                                              of the tuple contains a dictionary of the documents, with
                                                              their filename as the key and the contents as the value.
        """
        # Basic check of mandatory arguments
        self._check_operation_name(operation_name=operation_name)

        headers = {"User-Agent": self.user_agent}
        client = Client(self.wsdl_url)

        # Add parameter plugin to handle parameters, when those are set
        if parameters is not None:
            client.set_options(plugins=[AddParametersPlugin(parameters)])

        # Add auth header for OAuth2 requests
        if isinstance(authentication, ClientCredential):
            headers["Authorization"] = f"Bearer {authentication.get_token(self.hostname)}"

        client.set_options(headers=headers)

        # Any parameters will be handled by the AddParametersPlugin, so don't pass them here
        # GetResult(xs:string Operation, Identification Identification, Parameters Parameters,
        #           Authentication Authentication)
        suds_response = client.service.GetResult(
            Operation=operation_name,
            Identification=self.identification,
            Parameters=None,
            Authentication=self._generate_auth_parameter(authentication),
        )

        # Raise Exceptions for known errors
        self._handle_response_errors(suds_response=suds_response)

        # Handle possibly received documents
        if (
            auto_handle_documents
            and hasattr(suds_response, "Report")
            and hasattr(suds_response.Report, "Documents")
            and isinstance(suds_response.Report.Documents, Text)
        ):
            # The the base64 encoded contents as a zip file
            documents_dict: dict[str, bytes] = {}

            with zipfile.ZipFile(io.BytesIO(base64.b64decode(str(suds_response.Report.Documents))), "r") as docs_zip:
                for zipped_file in docs_zip.filelist:
                    documents_dict[zipped_file.filename] = docs_zip.read(zipped_file.filename)

            # Cleanup variable without further use
            del docs_zip
            if "zipped_file" in locals():
                del zipped_file  # pylint: disable=W0631

            # Delete the Document node from the sudsobject
            del suds_response.Report.Documents

            result = (suds_response, documents_dict)

        else:
            result = suds_response

        return result

    @staticmethod
    def _generate_data_xml(data: list[dict[str, str]]) -> Document:
        # Build data xml
        root = Element("Import")
        doc = Document(root)

        for data_row in data:
            row = Element("Row", parent=root)
            for key, value in data_row.items():
                row.set(name=key, value=value)
            root.append(row)

        return doc

    @staticmethod
    def _generate_zip_b64(
        prepared_data: str | Document,
        documents: list[str],
        file_basename: str,
        file_extension: str,
        keep_zip_file: bool,
    ) -> str:
        # Generate the full filename for the zip file
        import_zip_path = os.path.join(tempfile.gettempdir(), f"{file_basename}.zip")

        # Create the zip file
        with zipfile.ZipFile(import_zip_path, "w") as import_zip:
            # Add all the supplied documents
            for document_path in documents:
                archive_name = os.path.join("Documents", os.path.split(document_path)[1])
                import_zip.write(filename=document_path, arcname=archive_name)

            # Add the data file
            if isinstance(prepared_data, Document):
                import_zip.writestr(zinfo_or_arcname=f"{file_basename}.{file_extension}", data=prepared_data.str())
            elif isinstance(prepared_data, str):
                import_zip.write(filename=prepared_data, arcname=os.path.split(prepared_data)[1])

            # log.debug(f"Zip-file created {import_zip_path}: \n{pprint.pformat(import_zip.namelist(), indent=2)}")
            log.debug("Zip-file created %s: \n%s", import_zip_path, pprint.pformat(import_zip.namelist(), indent=2))

        # Cleanup references to the ZipFile
        del import_zip

        # Convert zipfile to base64
        with open(import_zip_path, "rb") as import_zip_file:
            data_str = base64.b64encode(import_zip_file.read()).decode("utf-8")

        # Remove the zip file from disk
        if not keep_zip_file:
            os.remove(import_zip_path)

        return data_str

    def run_import(
        self,
        operation_name: str,
        data: str | list[dict[str, str]],
        authentication: None | str | ClientCredential = None,
        file_name: None | str = None,
        documents: None | list[str] = None,
        auto_parse_response: bool = True,
    ) -> ImportResult | SudsObject:
        """Retrieve results from a "Server for providing data" in Relatics, with checking of the results

        "data" can be given in the following formats:
        * a `str` with the name of the data file. Can be an Excel file or csv file.
        * a `list` of `dict[str, str]`, for example:
          ```python
          data=[
              {"name": "Object 1", "description": "Lorem ipsum dolor sit amet."},
              {"name": "Object 2", "description": "Ut enim ad minim veniam."},
          ]
          ```

        Args:
            operation_name : The "OperationName" of the webservice to call
            data : The data to send to the import. See description above.
            authentication : Authentication for the webservice, either:
                             * None for no authentication,
                             * str for entryCode authentication or
                             * ClientCredential for OAuth2 client credentials
            file_name : Filename send to Relatics. Will show up in the "Imported file" column in the import log. If
                        no extension is given or the extension doesn't match the supplied data, the correct extension
                        will be added
            documents : Optional list of filepaths to include in the import. Must be unique names.
                See https://kb.relaticsonline.com/published/ShowObject.aspx?Key=7126fb9d-58df-e311-9406-00155de0940e
            auto_parse_response : Convert the return object for easy access

        Raises:
            InvalidOperationError: When an invalid operation_name is supplied
            InvalidWorkspaceError: When an invalid workspace_id is supplied

        Returns:
            ImportResult : Result object when the retrieved response is parsed
            suds.sudsobject.Object : The retrieved response, when not parsed
        """
        # Basic check of mandatory arguments
        self._check_operation_name(operation_name=operation_name)
        if not data:
            # Above "if" checks for both empty str or empty list,
            # see https://docs.python.org/3/library/stdtypes.html#truth-value-testing
            raise ValueError("Supplied data is empty.")
        if documents:
            # Detect duplicate names. Remove duplicate tails in the path with set(). Optimized with set comprehension.
            if len({os.path.split(path)[1] for path in documents}) != len(documents):
                raise ValueError("Duplicate filenames in document list.")

        headers = {"User-Agent": self.user_agent}
        file_extension = None

        client = Client(self.wsdl_url)

        # Prepare the data part
        if isinstance(data, list):
            # Set appropriate filename
            file_extension = "xml"

            # Build data xml
            prepared_data = self._generate_data_xml(data)

        elif isinstance(data, str):
            # Set appropriate filename, based on the given filename in "data"
            file_extension = os.path.splitext(data)[1][1:]

            # Validate if given extensions is supported
            if file_extension not in SUPPORTED_EXTENSIONS:
                raise TypeError("Supplied file has unsupported file extension.")

            prepared_data = data

        else:
            raise TypeError("Invalid type of data supplied.")

        # Set appropriate filename
        if file_name is None:
            file_basename = f"{IMPORT_BASENAME}"
        else:
            # Clean any possible path from the filename and remove a possible extension
            file_basename = os.path.splitext(os.path.split(file_name)[1])[0]

        # Choose how to create the base64 data: when document are supplied, create a zip; otherwise
        # use the file or xml data
        if documents is not None:
            # Generate the base64 encoded zip-file
            data_str = self._generate_zip_b64(
                prepared_data=prepared_data,
                documents=documents,
                file_basename=file_basename,
                file_extension=file_extension,
                keep_zip_file=self.keep_zip_file,
            )

            # Set the file extension to zip
            file_extension = "zip"

        else:  # documents is None
            if isinstance(data, list):
                # Convert previously generated xml to base64
                data_str = base64.b64encode(bytes(prepared_data.str(), "utf-8")).decode("utf-8")

            elif isinstance(data, str):
                # Convert supplied data file to base64
                with open(data, "rb") as data_file:
                    data_str = base64.b64encode(data_file.read()).decode("utf-8")

        # Add auth header for OAuth2 requests
        if isinstance(authentication, ClientCredential):
            headers["Authorization"] = f"Bearer {authentication.get_token(self.hostname)}"

        client.set_options(headers=headers)

        # Import(xs:string Operation, Identification Identification, Authentication Authentication, xs:string Filename,
        #        xs:string Data)
        suds_response = client.service.Import(
            Operation=operation_name,
            Identification=self.identification,
            Authentication=self._generate_auth_parameter(authentication),
            Filename=f"{file_basename}.{file_extension}",
            Data=data_str,
        )
        # KNOWLEDGE: Convert sudsobject to dict: client.dict(sudsobject)

        # Raise Exceptions for known errors
        self._handle_response_errors(suds_response=suds_response)

        if auto_parse_response:
            # Parse the raw response into something useful
            import_result = ImportResult.from_suds(suds_response)
        else:
            import_result = suds_response

        return import_result
