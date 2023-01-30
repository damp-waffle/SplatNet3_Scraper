class MockResponse:
    def __init__(
        self,
        status_code: int,
        text: str = "",
        json: dict = {},
        url: str = "",
    ) -> None:
        self._status_code = status_code
        self.status_code_counter = 0
        self._text = text
        self.text_counter = 0
        self._json = json
        self.json_counter = 0
        self._url = url
        self.url_counter = 0

    @property
    def status_code(self):
        self.status_code_counter += 1
        return self._status_code

    @property
    def text(self):
        self.text_counter += 1
        return self._text

    def json(self):
        self.json_counter += 1
        return self._json

    @property
    def url(self):
        self.url_counter += 1
        return self._url


class MockNSO:
    def __init__(self) -> None:
        self._mocked = True
        self._session_token = None
        self._user_info = None
        self._gtoken = None
        self._invalid_tokens = []

    @property
    def session_token(self):
        return self._session_token

    def get_gtoken(self, *args) -> str:
        if "gtoken" in self._invalid_tokens:
            return ""

        self._gtoken = "test_gtoken"
        self._user_info = {
            "country": "test_country",
            "language": "test_language",
        }
        return self._gtoken

    def get_bullet_token(self, *args) -> str:
        if "bullet_token" in self._invalid_tokens:
            return ""

        return "test_bullet_token"

    @staticmethod
    def new_instance():
        return MockNSO()


class MockTokenManager:
    def __init__(self, origin: dict = {}) -> None:
        self._mocked = True
        self._origin = origin

    @staticmethod
    def load():
        return MockTokenManager()

    @staticmethod
    def from_config_file(*args, **kwargs):
        return MockTokenManager()


class MockConfigParser:
    def __init__(self) -> None:
        self._mocked = True
        self._sections = {"options": {}}

    def __getitem__(self, key):
        return self._sections[key]

    def __setitem__(self, key, value):
        self._sections[key] = value

    def __contains__(self, key):
        return key in self._sections

    def __iter__(self):
        return iter(self._sections)

    def __len__(self):
        return len(self._sections)

    def add_section(self, section):
        self._sections[section] = {}

    def remove_section(self, section):
        del self._sections[section]

    def has_section(self, section):
        return section in self._sections

    def options(self, section):
        return list(self._sections[section].keys())

    def remove_option(self, section, option):
        del self._sections[section][option]
