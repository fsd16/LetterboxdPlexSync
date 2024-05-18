import logging
import requests
from en_pyurl import URL


class Overseerr:
    def __init__(self, server, api_key):
        self.LOG = logging.getLogger(__name__)
        self.base_url = URL(server) / "api" / "v1"

        auth_header = {"X-Api-Key": api_key}

        self._session = requests.Session()
        self._session.headers.update(auth_header)

    def request(self, tmdb: int):
        self.LOG.info(f"Requesting movie: {tmdb}")

        data = {
            "mediaType": "movie",
            "mediaId": tmdb,
            "is4k": False,
        }

        res = self._session.post(self.base_url / "request", json=data)
        match res.status_code:
            case 201:
                self.LOG.info(f"Request for {tmdb} was successful")
                return True
            case 409:
                self.LOG.warning(f"Request for {tmdb} already exists")
                return False
            case _:
                self.LOG.error(f"Request for {tmdb} failed: {res.status_code}")
                return False

    def media(self):
        self.LOG.info(f"Fetching media")

        params = {
            "take": 20,
            "skip": 0
        }

        all_movies = []  # Initialize an empty list to store all movies

        while True:
            res = self._session.get(self.base_url / "media", params=params)
            res_json = res.json()

            # Extend the list with results from the current page
            all_movies.extend(res_json["results"])

            # Check if there's a next page
            if res_json["pageInfo"]["page"] < res_json["pageInfo"]["pages"]:
                params["skip"] += params["take"]  # Increment the skip value
            else:
                break  # No more pages, exit the loop

        return all_movies
