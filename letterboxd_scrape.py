from concurrent.futures import Future, ThreadPoolExecutor, wait
from dataclasses import dataclass
from getpass import getpass, getuser
from http.cookiejar import CookieJar
import io
from json import dumps
import logging
from pathlib import Path
import pickle
import re
import sys
from typing import Any, Callable, Sequence, TypeVar
import arrow
from numpy import int64
from pandas import DataFrame, concat, notna, read_csv, read_html
import requests
from requests.cookies import RequestsCookieJar
import os
import functools

import bs4
from en_pyurl import URL


def dump(data: str):
    with open("dump.txt", 'w') as f:
        f.write(data)


class LoginError(Exception):
    pass


class LetterBoxd:
    host: URL | str = "https://letterboxd.com"
    username: str = "fdrabsch"
    password: str = ""
    _cookie_path: Path | str = (
            Path(os.getenv("tmp", "/tmp")).resolve() / "letterboxd_cookies.pickle"
    )
    session = requests.Session()

    def __init__(self) -> None:
        self.LOG = logging.getLogger(__name__)

        self.cookie_path = self._cookie_path
        self._host = URL(self.host)

        # self.login()

        self.device_data_cache = dict()
        self.envoy_data_cache = dict()

    @classmethod
    def clear_cookies(cls):
        if Path(cls._cookie_path).exists():
            os.remove(cls._cookie_path)
            return True
        else:
            return False

    @property
    def cookie_path(self):
        return Path(self._cookie_path)

    @cookie_path.setter
    def cookie_path(self, value):
        self._cookie_path = value

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

    def __enter__(self):
        self.login()
        return self

    def __exit__(self, t, v, tb):
        # self.get_pcu_details.cache_clear()
        pass

    def __del__(self):
        self.cookie_path = self.session.cookies


if __name__ == "__main__":
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)
    handler = logging.StreamHandler()
    formatter = logging.Formatter(f"%(name)s - %(levelname)s - %(message)s")
    handler.setFormatter(formatter)
    handler.setLevel(logging.DEBUG)
    logger.addHandler(handler)

    LetterBoxd.username = "fdrabsch"
    LetterBoxd.password = "38Canis12"

    with LetterBoxd() as scrape:
        print(scrape.get_watchlist())
