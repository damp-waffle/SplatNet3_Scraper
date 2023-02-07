import configparser
from typing import Literal, overload

from splatnet3_scraper.base.tokens import Token, TokenManager
from splatnet3_scraper.constants import DEFAULT_USER_AGENT, IMINK_URL


class Config:
    """Class that can access the token manager as well as additional options."""

    def __init__(
        self,
        config_path: str | None = None,
        *args,
        token_manager: TokenManager | None = None,
    ) -> None:
        """Initializes the class. If token_manager is given, it will assume that
        this is a first time initialization and has not been setup yet.

        Token manager will look for tokens in the following order:
            1. the config_path argument
            2. check the current working directory for ".splatnet3_scraper"
            3. check for environment variables for defined tokens
            4. check the current working directory for "tokens.ini"

        If none of these are found, an exception will be raised.

        Args:
            config_path (str | None): The path to the config file. If None, it
                will look for ".splatnet3_scraper" in the current working
                directory. Defaults to None.
            *args: These are ignored.
            token_manager (TokenManager | None): The token manager to use.
                Keyword argument. If given, it will skip the post-init method.
                Defaults to None.
        """
        if token_manager is None:
            self.__post_init__(config_path)
            return
        else:
            self.config_path = config_path

        self.token_manager = token_manager
        self.config = configparser.ConfigParser()
        self.config.add_section("options")
        self.options = self.config.options("options")

    def __post_init__(self, config_path: str | None = None) -> None:
        """This function is called after the __init__ method and is used to
        allow the Config class to be initialized with a TokenManager instance,
        which is useful for initial setup.

        Args:
            config_path (str | None): The path to the config file. If None, it
                will look for ".splatnet3_scraper" in the current working
                directory.
        """
        if config_path is not None:
            self.token_manager = TokenManager.from_config_file(config_path)
        # cgarza: A little bit of redundancy here, need better method.
        else:
            self.token_manager = TokenManager.load()

        config_path = (
            ".splatnet3_scraper" if config_path is None else config_path
        )

        self.config_path = config_path
        self.config = configparser.ConfigParser()
        self.config.read(config_path)
        try:
            self.options = self.config.options("options")
        except configparser.NoSectionError:
            self.config.add_section("options")
            self.options = self.config.options("options")
        self.manage_options()

        with open(config_path, "w") as configfile:
            self.config.write(configfile)

    @staticmethod
    def from_env() -> "Config":
        """Creates a Config instance using the environment variables.

        Returns:
            Config: The Config instance.
        """
        return Config(token_manager=TokenManager.from_env())
    
    @staticmethod
    def from_s3s_config(config_path: str) -> "Config":
        """Creates a Config instance using the config file from s3s.

        Args:
            config_path (str): The path to the config file.

        Returns:
            Config: The Config instance.
        """
        return Config(token_manager=TokenManager.from_text_file(config_path))

    def save(
        self, path: str | None = None, include_tokens: bool = True
    ) -> None:
        """Saves the config file to the given path.

        Args:
            path (str | None): The path to save the config file to. If the token
                manager is using environment variables, the tokens section will
                be removed from the config file. If None, it will save to the
                path given in the constructor or ".splatnet3_scraper" in the
                current working directory.
            include_tokens (bool): Whether or not to include the tokens in the
                config file. If False, the tokens will be removed from the
                config file.
        """
        # Check if the user has the tokens in a separate file
        origin = self.token_manager._origin["origin"]
        if (origin == "env") or (not include_tokens):
            # Remove the token manager from the config file
            self.config.remove_section("tokens")
        if path is None and self.config_path is not None:
            path = self.config_path
        elif path is None:
            path = ".splatnet3_scraper"

        with open(path, "w") as configfile:
            self.config.write(configfile)

    def manage_options(self) -> None:
        """Manage the options in the config file.

        This function will move invalid options to the "unknown" section and
        move deprecated options to the "deprecated" section while replacing them
        with the new option name.
        """
        for option in self.options:
            if option not in (
                self.ACCEPTED_OPTIONS + list(self.DEPRECATED_OPTIONS.keys())
            ):
                if not self.config.has_section("unknown"):
                    self.config.add_section("unknown")
                self.config["unknown"][option] = self.config["options"][option]
                self.config.remove_option("options", option)
            if option in self.DEPRECATED_OPTIONS:
                deprecated_name = option
                option_name = self.DEPRECATED_OPTIONS[option]
                if not self.config.has_section("deprecated"):
                    self.config.add_section("deprecated")
                # Make a copy of the deprecated option in the deprecated section
                # and then replace the deprecated option with the new option
                self.config["deprecated"][deprecated_name] = self.config[
                    "options"
                ][deprecated_name]
                self.config["options"][option_name] = self.config["options"][
                    deprecated_name
                ]
                self.config.remove_option("options", option)

    ACCEPTED_OPTIONS = [
        "user_agent",
        "log_level",
        "log_file",
        "export_path",
        "language",
        "lang",
        "country",
        "stat.ink_api_key",
        "stat_ink_api_key",
        "statink_api_key",
        "f_token_url",
    ]

    DEPRECATED_OPTIONS = {
        "api_key": "stat.ink_api_key",
        "f_gen": "f_token_url",
    }

    DEFAULT_OPTIONS = {
        "user_agent": DEFAULT_USER_AGENT,
        "f_gen": IMINK_URL,
        "export_path": "",
    }

    def get(self, key: str) -> str:
        """Get the value of an option. If the option is not set, the default
        value will be returned.

        Args:
            key (str): The name of the option.

        Raises:
            KeyError: If the option is valid, but not set and has no default.
            KeyError: If the option is not valid.

        Returns:
            str: The value of the option.
        """
        if key in self.ACCEPTED_OPTIONS:
            if key in self.config["options"]:
                return self.config["options"][key]
            elif key in self.DEFAULT_OPTIONS:
                return self.DEFAULT_OPTIONS[key]
            else:
                raise KeyError(f"Option not set and has no default: {key}")
        elif key in self.DEPRECATED_OPTIONS:
            return self.get(self.DEPRECATED_OPTIONS[key])
        else:
            raise KeyError(f"Invalid option: {key}")

    def get_data(self, key: str) -> str:
        if not self.config.has_section("data"):
            self.config.add_section("data")
            data = self.token_manager.data
            for k, v in data.items():
                self.config["data"][k] = v
        return self.config["data"][key]

    @overload
    def get_token(self, key: str, full_token: Literal[False] = ...) -> str:
        ...

    @overload
    def get_token(self, key: str, full_token: Literal[True]) -> Token:
        ...

    @overload
    def get_token(self, key: str, full_token: bool) -> str | Token:
        ...

    def get_token(self, key: str, full_token: bool = False) -> str | Token:
        """Get the value of a token.

        Args:
            key (str): The name of the token.
            full_token (bool): Whether or not to return the full token. If
                False, only the token value will be returned.

        Returns:
            str: The value of the token.
        """
        return self.token_manager.get(key, full_token)
