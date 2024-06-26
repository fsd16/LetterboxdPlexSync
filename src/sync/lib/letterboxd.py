import io
import json
import logging
import os
import pickle
import re
from getpass import getpass
from pathlib import Path

import requests
from pandas import read_csv
from requests.cookies import RequestsCookieJar
from sync.lib.pyurl import URL

LOG = logging.getLogger(__name__)

class LoginError(Exception):
    pass


class LetterBoxd:
    host: URL | str = "https://letterboxd.com"
    username: str = ""
    password: str = ""
    cache_dir: Path = Path(__file__).resolve().parent.parent / "data"
    session = requests.Session()

    def __init__(self) -> None:
        self.LOG = logging.getLogger(__name__)

        assert all([self.username, self.password]), "Attributes 'username' and 'password' must be set before instantiating class"
        self.cache_dir.mkdir(exist_ok=True)

        self.cookie_path = self.cache_dir / "letterboxd_cookies.pickle"
        self.tmdbid_cache = self.cache_dir / "boxdurltotmdb.cache"

        self._host = URL(self.host)

    @classmethod
    def clear_cookies(cls):
        cache_file = cls.cache_dir / "letterboxd_cookies.pickle"
        if cache_file.exists():
            os.remove(cache_file)
            return True
        else:
            return False

    @property
    def cached_cookies(self) -> RequestsCookieJar | None:
        if self.cookie_path.exists():
            with open(self.cookie_path, "rb") as f:
                cookie = RequestsCookieJar()
                cookie.update(pickle.load(f))
            return cookie
        else:
            return None

    @cached_cookies.setter
    def cached_cookies(self, value: RequestsCookieJar):
        with open(self.cookie_path, "wb") as f:
            pickle.dump(value, f)

    def login(self):
        if self.session.cookies:
            response = self.session.get(self._host)
            if response.url != self._host:
                self.LOG.debug("Failed to log in using session cookies")
                self.session.cookies.clear()
                self.login()
            else:
                self.LOG.debug("Logged in successfully using session cookies")
        elif self.cached_cookies is not None:
            self.session.cookies.update(self.cached_cookies)

            logged_url = self._host / 'loggedin'
            response = self.session.get(logged_url)

            if response.url != self._host:
                self.LOG.debug("Failed to log in using cached cookies")
                res = self.clear_cookies()
                if not res:
                    raise LoginError(f"Failed to clear cached cookies at: {self.cookie_path}")
                self.login()
            else:
                self.LOG.debug("Logged in successfully using cached cookies")
        else:
            login_url = self._host / 'user' / 'login.do'

            # Prompt user for password
            if not self.password:
                LetterBoxd.password = getpass(f"Enter password for {self.username}: ")

            self.session.get(self._host)
            token = self.session.cookies['com.xk72.webparts.csrf']

            post_data = {
                '__csrf': token,
                'username': self.username,
                'password': self.password
            }
            headers = {'Referer': self._host}

            response = self.session.post(login_url, data=post_data, headers=headers)

            if response.status_code != 200:
                raise LoginError(f"Failed to log in using user credentials. Status Code: {response.status_code}")
            elif response.json()['result'] != 'success':
                raise LoginError(f"Failed to log in using user credentials. Result: {response.json()['result']}")
            else:
                self.LOG.debug("Logged in successfully using user credentials")

            self.cached_cookies = self.session.cookies

    def get(self, url: str | URL, *args, **kwargs):

        if not url.startswith(self._host):
            url = self._host / url

        self.LOG.debug(f"Sending GET request to: {url}")
        # Perform download request
        response = self.session.get(url, *args, **kwargs)

        return response

    def get_watchlist(
            self,
    ):

        self.LOG.info(f"Getting watchlist for {self.username}")
        headers = {
            "content-type": "text/csv;charset=utf-8"
        }
        response = self.get(
            f"{self.username}/watchlist/export/",
            headers=headers
        )
        # print(response.text)
        df = read_csv(io.StringIO(response.text))
        return df

    def get_tmdbid(self, url):
        if Path(self.tmdbid_cache).exists():
            with open(self.tmdbid_cache, 'r') as fp:
                cache = json.load(fp)
        else:
            cache = {}

        if url in cache:
            return cache[url]

        response = self.session.get(url)

        match = re.search(r'data-tmdb-id="(\d+)"', response.text)
        if match:
            tmdbid = match.group(1)
            cache[url] = tmdbid

            with open(self.tmdbid_cache, 'w') as fp:
                json.dump(cache, fp, indent=4)

            return tmdbid

    def __enter__(self):
        self.login()
        return self

    def __exit__(self, t, v, tb):
        pass

    def __del__(self):
        self.cached_cookies = self.session.cookies

if __name__ == "__main__":
    u = URL("https://www.reddit.com/r/radarr/comments/1ban3dc/introducing_swaparr_handling_stalled_torrents_in/")
    print(u)