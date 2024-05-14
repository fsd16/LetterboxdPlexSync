import logging
from pathlib import Path

from src.sync.lib.letterboxd import LetterBoxd
from src.sync.lib.overseerr import Overseerr
from dotenv import load_dotenv
from getenv import Env

LOG = logging.getLogger(__name__)

env_path = Path("../../.env")

load_dotenv(env_path)

Env.set_prefix("OVERSEERR")
OVERSEERR_HOST = Env("{prefix}_HOST")
OVERSEERR_API_KEY = Env("{prefix}_API_KEY")

Env.set_prefix("LBXD")
LBXD_USERNAME = Env("{prefix}_USERNAME")
LBXD_PASSWORD = Env("{prefix}_PASSWORD")

if __name__ == "__main__":
    LOG.setLevel(logging.DEBUG)
    handler = logging.StreamHandler()
    handler.setLevel(logging.DEBUG)
    LOG.addHandler(handler)

    LetterBoxd.username = LBXD_USERNAME.get()
    LetterBoxd.password = LBXD_PASSWORD.get()

    with LetterBoxd() as scrape:

        wl = scrape.get_watchlist()

        ids = []
        for url in wl["Letterboxd URI"]:
            ids.append(int(scrape.get_tmdbid(url)))

    overseerr = Overseerr(OVERSEERR_HOST.get(), OVERSEERR_API_KEY.get())

    for tmdb_id in ids:
        print(overseerr.request(tmdb_id))
        break

    # movies = overseerr.media()
    #
    # ids = [m["tmdbId"] for m in movies if m["mediaType"] == "movie"]
    # print(ids)
    # print(len(ids))