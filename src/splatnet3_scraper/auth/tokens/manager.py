import configparser
import json
import logging
import os
import re
import time
from typing import Any, Literal, cast, overload

import requests

from splatnet3_scraper import __version__
from splatnet3_scraper.auth.exceptions import (
    FTokenException,
    NintendoException,
    SplatNetException,
)
from splatnet3_scraper.auth.graph_ql_queries import queries
from splatnet3_scraper.auth.nso import NSO
from splatnet3_scraper.auth.tokens.environment_manager import (
    EnvironmentVariablesManager,
)
from splatnet3_scraper.auth.tokens.keychain import TokenKeychain
from splatnet3_scraper.auth.tokens.token_typing import ORIGIN
from splatnet3_scraper.auth.tokens.tokens import Token
from splatnet3_scraper.constants import (
    ENV_VAR_NAMES,
    GRAPH_QL_REFERENCE_URL,
    IMINK_URL,
    TOKEN_EXPIRATIONS,
    TOKENS,
)
from splatnet3_scraper.utils import retry

logger = logging.getLogger(__name__)


class ManagerOrigin:
    def __init__(self, origin: ORIGIN, data: str | None = None) -> None:
        self.origin = origin
        self.data = data


class TokenManager:
    """Manages the tokens used for authentication. Handles regeneration and
    interaction with the keychain. This class is meant to mostly be used via its
    "get" method
    """

    def __init__(
        self,
        nso: NSO | None = None,
        f_token_url: str | list[str] | None = None,
        *,
        env_manager: EnvironmentVariablesManager | None = None,
        origin: ORIGIN = "memory",
        origin_data: str | None = None,
    ) -> None:
        """Initializes a ``TokenManager`` object. The ``TokenManager`` object
        handles the tokens used for authentication. It handles regeneration and
        interaction with the keychain. This class is meant to mostly be used via
        its "get" method.

        Args:
            nso (NSO | None): An instance of the ``NSO`` class. If one is not
                provided, a new instance will be created. Defaults to None.
            f_token_url (str | list[str] | None): The URL(s) to use to generate
                tokens. If a list is provided, each URL will be tried in order
                until a token is successfully generated. If None is provided,
                the default URL provided by imink will be used. Defaults to
                None.
            env_manager (EnvironmentVariablesManager | None): An instance of the
                ``EnvironmentVariablesManager`` class. If one is not provided, a
                new instance will be created. Defaults to None.
            origin (ORIGIN): The origin of the tokens. Defaults to "memory". One
                of "memory", "env", or "file".
            origin_data (str | None): The data associated with the origin. If
                the origin is "memory" or "env", this is ignored. If the origin
                is "file", this should be the path to the file. Defaults to
                None.
        """
        nso = nso or NSO.new_instance()
        self.nso = nso
        if f_token_url is None:
            self.f_token_url = [IMINK_URL]
        elif isinstance(f_token_url, str):
            self.f_token_url = [f_token_url]
        else:
            self.f_token_url = f_token_url

        self.keychain = TokenKeychain()
        self.env_manager = env_manager or EnvironmentVariablesManager()
        self.origin = ManagerOrigin(origin, origin_data)

    def flag_origin(self, origin: ORIGIN, data: str | None = None) -> None:
        """Flags the origin of the token manager. This is used to identify where
        the token manager was loaded from, if anywhere. This is used to help
        keep track of whether the user wants to save the tokens to disk or not,
        but can potentially be used for other things in the future. This is
        called automatically when the token manager is loaded from a config
        file or environment variables. Subsequent calls to this method will
        overwrite the previous origin.

        Args:
            origin (str): The origin of the token manager.
            data (str | None): Additional data about the origin. For example,
                if the token manager was loaded from a config file, this would
                be the path to the config file. On the other hand, if the token
                manager was loaded from environment variables, this would be
                None.
        """
        logger.debug("Flagging origin %s with data %s", origin, data)
        self.origin = ManagerOrigin(origin, data)

    def add_token(
        self,
        token: str | Token,
        name: str | None = None,
        timestamp: float | None = None,
    ) -> None:
        """Adds a token to the keychain. If the token is a string, the name of
        the token must be provided. If the token is a ``Token`` object, the
        name of the token will be used.

        Args:
            token (str | Token): The token to add to the keychain.
            name (str | None, optional): The name of the token. Only required if
                the token is a string. Defaults to None.
            timestamp (float | None, optional): The timestamp of the token.
                Defaults to None.

        Raises:
            ValueError: If the token is a string and the name of the token is
                not provided.
        """
        try:
            new_token = self.keychain.add_token(token, name, timestamp)
        except ValueError as e:
            raise e

        logger.debug("Added token %s to keychain", new_token.name)
        if new_token.name == TOKENS.GTOKEN:
            self.nso._gtoken = new_token.value
        elif new_token.name == TOKENS.SESSION_TOKEN:
            self.nso._session_token = new_token.value
