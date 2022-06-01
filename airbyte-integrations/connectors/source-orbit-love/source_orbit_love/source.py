#
# Copyright (c) 2021 Airbyte, Inc., all rights reserved.
#
import logging
from abc import ABC
from typing import Any, Iterable, List, Mapping, MutableMapping, Optional, Tuple, Dict, cast

import requests
import urllib.parse
from airbyte_cdk.sources import AbstractSource
from airbyte_cdk.sources.streams import Stream
from airbyte_cdk.sources.streams.http import HttpStream
from airbyte_cdk.sources.streams.http.auth import TokenAuthenticator


# Basic full refresh stream
class OrbitLoveStream(HttpStream, ABC):
    def __init__(self, workspace_slug: str, items_per_page=100, **kwargs):
        super().__init__(**kwargs)
        self.workspace_slug = workspace_slug
        self.items_per_page = items_per_page

    @property
    def url_base(self) -> str:
        return f"https://app.orbit.love/api/v1/{self.workspace_slug}/"

    def next_page_token(self, response: requests.Response) -> Optional[Mapping[str, Any]]:
        decoded_response = response.json()
        links = decoded_response.get("links")
        if not links:
            return

        next = links.get("next")
        if not next:
            return

        next_url = urllib.parse.urlparse(next)
        next_params = list((cast(str, k), v) for (k, v) in urllib.parse.parse_qsl(next_url.query))
        return next_params

    def request_params(
        self, stream_state: Mapping[str, Any], stream_slice: Mapping[str, any] = None, next_page_token: Mapping[str, Any] = None
    ) -> MutableMapping[str, Any]:
        params = {"items": self.items_per_page}
        if next_page_token is not None:
            params.update(next_page_token)
        return params


class MembersWithIdentities(OrbitLoveStream):
    primary_key = "id"

    def path(
        self, stream_state: Mapping[str, Any] = None, stream_slice: Mapping[str, Any] = None, next_page_token: Mapping[str, Any] = None
    ) -> str:
        return "members"

    @staticmethod
    def __build_identity(relid_to_identities: Dict, identity_id: str):
        identity = relid_to_identities[identity_id]
        identity["id"] = identity_id
        return identity

    @classmethod
    def __add_identities_to_member(cls, member_info: Dict, relid_to_identities):
        relationships = member_info["relationships"]["identities"]["data"]
        identities = [cls.__build_identity(relid_to_identities, rel["id"]) for rel in relationships]
        attributes = member_info["attributes"]
        attributes["identities"] = identities
        return attributes

    def parse_response(self, response: requests.Response, **kwargs) -> Iterable[Mapping]:
        """
        :return an iterable containing each record in the response
        """
        response_json = response.json()
        relid_to_identities = {d["id"]: d["attributes"] for d in response_json["included"]}
        members = response_json["data"]
        return [self.__add_identities_to_member(m, relid_to_identities) for m in members]

# Source
class SourceOrbitLove(AbstractSource):
    def check_connection(self, logger, config) -> Tuple[bool, any]:
        try:
            url = f"https://app.orbit.love/api/v1/{config['workspace_slug']}/organizations"
            headers = {
                "Accept": "application/json",
                "Authorization": f"Bearer {config['api_key']}"
            }
            response = requests.request("GET", url, headers=headers)
            response.raise_for_status()
            return True, None
        except Exception as e:
            logging.exception("bad api_key or workspace_slug", exc_info=e)
            return False, e

    def streams(self, config: Mapping[str, Any]) -> List[Stream]:
        auth = TokenAuthenticator(token=config['api_key'])
        return [MembersWithIdentities(workspace_slug=config['workspace_slug'], authenticator=auth)]
