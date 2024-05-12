from pathlib import Path
import sys
from oauthlib.oauth2 import BackendApplicationClient
from requests_oauthlib import OAuth2Session
from dotenv import load_dotenv
from getenv import Env

env_path = Path(".env")

load_dotenv(env_path)

Env.set_prefix("LBXD")

LBXD_USERNAME = Env("{prefix}_USERNAME")
print(LBXD_USERNAME.get())
sys.exit()

# Set up your OAuth2 credentials
client_id = "your_client_id"
client_secret = "your_client_secret"
token_url = "https://example.com/oauth/token"  # Replace with your token URL

# Create an OAuth2 session
client = BackendApplicationClient(client_id=client_id)
oauth = OAuth2Session(client=client)
token = oauth.fetch_token(
    token_url=token_url, client_id=client_id, client_secret=client_secret
)

# Now you can use the access token for API requests
response = oauth.get("https://api.example.com/some_endpoint")
print(response.json())
