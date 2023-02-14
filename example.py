"""
Some examples on how to use the package
"""
import logging

from pyrelatics_webservices import ClientCredential, RelaticsWebservices

# pylint: disable=E0401,E0611
from pyrelatics_webservices.config import (  # type: ignore
    SAMPLE_CLIENT_ID,
    SAMPLE_CLIENT_SECRET,
    SAMPLE_COMPANY,
    SAMPLE_WORKSPACE_ID,
)

# pylint: enable=E0401,E0611

LOG_FORMAT = "%(asctime)s %(name)s %(levelname)s %(message)s"

logging.basicConfig(level=logging.INFO, format=LOG_FORMAT)
# logging.getLogger("suds.client").setLevel(logging.DEBUG)
logging.getLogger("pyrelatics_webservices.client").setLevel(logging.DEBUG)


cc = ClientCredential(
    client_id=SAMPLE_CLIENT_ID,
    client_secret=SAMPLE_CLIENT_SECRET,
)
relatics_webservice = RelaticsWebservices(SAMPLE_COMPANY, SAMPLE_WORKSPACE_ID)

# aaa = relatics_webservice.get_result(
#     operation_name="getActiesEntrycode",
#     parameters={"param1": "Hallo123_EntryCode"},
#     authentication="B7CAA7A9F27BCA0B6586A607DEDE31F0",
# )
# print(aaa)

# bbb = relatics_webservice.get_result(
#     operation_name="getActiesOauth2",
#     parameters={"param1": "Hallo123_Oauth2"},
#     authentication=cc,
# )
# print(bbb)

# ccc = relatics_webservice.get_result(
#     operation_name="getActiesNoAuth",
#     parameters={"param1": "Hallo123_NoAuth"},
#     authentication=None,
# )
# print(ccc)

relatics_webservice.keep_zip_file = True
# ddd = relatics_webservice.run_import(
#     operation_name="importeerActiesEntrycode",
#     data=[
#         {"name": "Actie EntryCode 01", "description": "Testing 12345"},
#         {"name": "Actie EntryCode 02", "description": "Testing 23456"},
#     ],
#     authentication="85477AF6F7A1B6CE797570648CF07037",
#     file_name="import_ddd.xml",
# )
# print(ddd)

# eee = relatics_webservice.run_import(
#     operation_name="importeerActiesOAuth2Client",
#     data=[
#         {"name": "Actie OAuth2 01", "description": "Testing 12345"},
#         {"name": "Actie OAuth2 02", "description": "Testing 23456"},
#     ],
#     authentication=cc,
#     file_name="import_eee.xml",
# )
# print(eee)

fff = relatics_webservice.run_import(
    operation_name="importeerActiesNoAuth",
    # data=[
    #     {"name": "Actie NoAuth 01", "description": "Testing 12345"},
    #     {"name": "Actie NoAuth 02", "description": "Testing 23456"},
    # ],
    # data="sample-data\\sample_without_references.xlsx",
    # data=[
    #     {
    #         "name": "Actie Ref 01",
    #         "description": "Testing 12345",
    #         "Reference": "sample-data\\cms.zeEf4OrA-collection_cover.jpeg",
    #     },
    #     {
    #         "name": "Actie Ref 02",
    #         "description": "Testing 23456",
    #         "Reference": "sample-data\\pexels-ksenia-chernaya-3965543.jpg",
    #     },
    # ],
    data="sample-data\\sample_with_references.xlsx",
    authentication=None,
    # file_name="import_fff.xml",
    file_name="import_fff",
    documents=[
        "sample-data\\cms.zeEf4OrA-collection_cover.jpeg",
        # "sample-data\\global-warming.jpg",
        "sample-data\\pexels-ksenia-chernaya-3965543.jpg",
        # "sample-data\\pexels-pavel-danilyuk-8442886.jpg",
    ],
)
print("\n\n#############################################   RESULT   #############################################")
print(fff)
