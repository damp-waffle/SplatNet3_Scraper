from __future__ import annotations

import configparser
from typing import Literal, overload

from splatnet3_scraper.auth.tokens import (
    EnvironmentVariablesManager,
    Token,
    TokenManager,
    TokenManagerConstructor,
)
from splatnet3_scraper.constants import TOKENS
from splatnet3_scraper.query.configuration.config_option_handler import (
    ConfigOptionHandler,
)


class Config:
    """The Config class is used to load, store, and manage the configuration
    options for the QueryHandler class. The Config class has a number of static
    methods that are used to create a new instance of the class, including from
    a file, from a few default options, etc. The bulk of the configuration
    options are stored in a ConfigParser object for uniformity and ease of use.
    It also functions as a high-level wrapper around the ``TokenManager`` class
    that enables the ``QueryHandler`` class to be quickly and easily
    instantiated, leading to less time spent configuring the ``QueryHandler``
    class and more time spent making queries.
    """

    DEFAULT_CONFIG_PATH = ".splatnet3_scraper"

    def __init__(
        self,
        handler: ConfigOptionHandler,
        *,
        token_manager: TokenManager | None = None,
        output_file_path: str | None = None,
    ) -> None:
        self._token_manager = token_manager
        self._output_file_path = output_file_path

        self.handler = handler

    @property
    def token_manager(self) -> TokenManager:
        """The ``TokenManager`` object used to manage the tokens. Acts as a
        TypeGuard for the ``_token_manager`` attribute.

        Raises:
            ValueError: If the token manager has not been initialized.

        Returns:
            TokenManager: The ``TokenManager`` object used to manage the tokens.
        """
        if self._token_manager is None:
            raise ValueError("Token manager not initialized.")
        return self._token_manager

    def regenerate_tokens(self) -> None:
        """Regenerates the tokens and updates the config."""
        self.token_manager.regenerate_tokens()
        # Add tokens to config
        for token in [
            TOKENS.SESSION_TOKEN,
            TOKENS.GTOKEN,
            TOKENS.BULLET_TOKEN,
        ]:
            self.handler.set_value(
                token,
                self.token_manager.get_token(token).value,
            )

    @property
    def session_token(self) -> str:
        """The session token.

        Returns:
            str: The session token.
        """
        return self.token_manager.get_token(TOKENS.SESSION_TOKEN).value

    @property
    def gtoken(self) -> str:
        """The gtoken.

        Returns:
            str: The gtoken.
        """
        return self.token_manager.get_token(TOKENS.GTOKEN).value

    @property
    def bullet_token(self) -> str:
        """The bullet token.

        Returns:
            str: The bullet token.
        """
        return self.token_manager.get_token(TOKENS.BULLET_TOKEN).value
