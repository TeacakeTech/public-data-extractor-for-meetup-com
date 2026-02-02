import json
import time

import jwt
import requests
import staticpipes.collection
import staticpipes.config
import staticpipes.pipe_base
import staticpipes.pipes.copy
import staticpipes.pipes.jinja2
import staticpipes.worker
from cryptography.hazmat.primitives import serialization

import publicdataextractorformeetupcom.site


class Worker:

    def __init__(
        self,
        meetup_com_authorized_member_id,
        meetup_com_your_client_key,
        meetup_com_private_signing_key,
    ):
        self._meetup_com_authorized_member_id = meetup_com_authorized_member_id
        self._meetup_com_your_client_key = meetup_com_your_client_key
        self._meetup_com_private_signing_key = meetup_com_private_signing_key
        self._meetup_com_access_token = None

    def _get_meetup_com_access_token(self):
        if self._meetup_com_access_token:
            # TODO we assume it's still valid - it may not be. We could check here.
            return

        # Make JWT
        private_key = serialization.load_pem_private_key(
            self._meetup_com_private_signing_key.encode(), password=None
        )
        payload = {
            "sub": self._meetup_com_authorized_member_id,
            "iss": self._meetup_com_your_client_key,
            "aud": "api.meetup.com",
            "exp": int(time.time()) + 600,  # Expires in 10 minutes
        }
        signed_jwt = jwt.encode(payload, private_key, algorithm="RS256")

        # Get Access Token
        url = "https://secure.meetup.com/oauth2/access"
        headers = {
            "Content-Type": "application/json",
        }
        data = {
            "grant_type": "urn:ietf:params:oauth:grant-type:jwt-bearer",
            "assertion": signed_jwt,
        }
        response = requests.post(url, json=data, headers=headers)
        response.raise_for_status()
        self._meetup_com_access_token = response.json().get("access_token")

    def _make_meetup_com_graphql_query(self, query, variables):
        graphql_url = "https://api.meetup.com/gql-ext"
        headers = {
            "Content-Type": "application/json",
            "Authorization": "Bearer {}".format(self._meetup_com_access_token),
        }
        response = requests.post(
            graphql_url, json={"query": query, "variables": variables}, headers=headers
        )
        response.raise_for_status()
        return response.json()

    def _get_group_data(self, group_url_name):

        self._get_meetup_com_access_token()

        return self._make_meetup_com_graphql_query(
            """
            query GetUpcomingEvents($groupURLName: String!) {
                groupByUrlname(urlname: $groupURLName) {
                    id
                    urlname
                    name
                    description
                    events {
                        edges {
                            node {
                                id
                                title
                                description
                                eventUrl
                                dateTime
                                duration
                                eventType
                                status
                                venues {
                                    name
                                    address
                                    postalCode
                                    country
                                    lat
                                    lon
                                }
                            }
                        }
                    }
                }
            }
            """,
            {"groupURLName": group_url_name},
        )

    def _write_group_data(self, group_data, out_directory):

        events_collection = staticpipes.collection.Collection()
        [
            events_collection.add_record(
                staticpipes.collection.CollectionRecord(d["node"]["id"], d["node"])
            )
            for d in group_data["data"]["groupByUrlname"]["events"]["edges"]
        ]

        config = staticpipes.config.Config(
            pipes=[
                PipeWriteRawData(group_data),
                staticpipes.pipes.jinja2.PipeJinja2(),
                staticpipes.pipes.copy.PipeCopy(extensions=["css"]),
            ],
            context={
                "group_id": group_data["data"]["groupByUrlname"]["id"],
                "group_urlname": group_data["data"]["groupByUrlname"]["urlname"],
                "group_name": group_data["data"]["groupByUrlname"]["name"],
                "group_description": group_data["data"]["groupByUrlname"][
                    "description"
                ],
                "collections": {"events": events_collection},
            },
        )

        worker = staticpipes.worker.Worker(
            config, publicdataextractorformeetupcom.site.DIRECTORY, out_directory
        )
        worker.build()

    def extract_group(self, group_url_name, out_directory):
        group_data = self._get_group_data(group_url_name)

        # Useful for testing
        # with open("out.json") as f:
        #    group_data = json.load(f)

        self._write_group_data(group_data, out_directory)


class PipeWriteRawData(staticpipes.pipe_base.BasePipe):

    def __init__(self, raw_data):
        super().__init__()
        self._raw_data = raw_data

    def start_build(self, current_info) -> None:
        self.build_directory.write(
            "/", "raw_data.json", json.dumps(self._raw_data, indent=4)
        )
