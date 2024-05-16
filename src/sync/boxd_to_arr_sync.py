import logging
from pathlib import Path

from .lib.letterboxd import LetterBoxd
from .lib.overseerr import Overseerr
from dotenv import load_dotenv, find_dotenv
from getenv import Env
from argparse import ArgumentParser

LOG = logging.getLogger(__name__)


def app():
    LOG.setLevel(logging.DEBUG)
    handler = logging.StreamHandler()
    handler.setLevel(logging.DEBUG)
    LOG.addHandler(handler)

    parser = ArgumentParser("BoxdArrSync", "Sync Letterboxd watchlist with Overseerr request list")
    parser.add_argument("-e", "--env", help="Path to .env")

    args = parser.parse_args()

    if args.env:
        env_path = Path(args.env).resolve()
    else:
        env_path = find_dotenv(raise_error_if_not_found=True)

    load_dotenv(env_path)
    LOG.debug(f"Environment variables loaded from: {env_path}")

    Env.set_prefix("OVERSEERR")
    overseerr_host = Env("{prefix}_HOST")
    overseerr_api_key = Env("{prefix}_API_KEY")

    Env.set_prefix("LBXD")
    lbxd_username = Env("{prefix}_USERNAME")
    lbxd_password = Env("{prefix}_PASSWORD")

    LetterBoxd.username = lbxd_username.get()
    LetterBoxd.password = lbxd_password.get()

    with LetterBoxd() as boxd:

        wl = boxd.get_watchlist()

        ids = []
        for url in wl["Letterboxd URI"]:
            tmdb_id = boxd.get_tmdbid(url)
            if tmdb_id:
                ids.append(int(tmdb_id))
            else:
                LOG.error(f"Failed to get TMDB ID for {url}")

    overseerr = Overseerr(overseerr_host.get(), overseerr_api_key.get())

    for tmdb_id in ids:
        overseerr.request(tmdb_id)


if __name__ == "__main__":
    app()
