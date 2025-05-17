import os.path
import sys

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from pathlib import Path

# If modifying these scopes, delete the file token.json.
SCOPES = ["https://www.googleapis.com/auth/documents.readonly"]

# The ID of a sample document.
DOCUMENT_ID = "1CEyOEqLL8fyFPsJZeVbC3ilGoEgyi7w96wPtW7pEpVs"


class MimifukuTrack:
    title: str
    contents: list[str]

    def __init__(self, title: str, contents: list[str]):
        self.title = title
        self.contents = contents


class MimifukuDeck:
    tracks: list[MimifukuTrack]

    def __init__(self, contents: list[str]):
        self.tracks = []
        contents = [s.strip() for s in contents if not s.isspace()]
        print(contents)
        i = 0
        while i < len(contents):
            title = contents[i].strip("#").strip()
            cur_texts: list[str] = []
            i += 1
            while i < len(contents) and not contents[i].startswith("#"):
                cur_texts.append(contents[i])
                i += 1
            if cur_texts:
                self.tracks.append(MimifukuTrack(title, cur_texts))


def tts(deck: MimifukuDeck) -> None:
    for track in deck.tracks:
        print(track.title)
        for text in track.contents:
            print(text)


def get_credentials(credentials_dir) -> Credentials:
    creds = None
    token_path = os.path.join(credentials_dir, "token.json")
    if os.path.exists(token_path):
        creds = Credentials.from_authorized_user_file(token_path, SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            credentials_path = os.path.join(credentials_dir, "credentials.json")
            flow = InstalledAppFlow.from_client_secrets_file(credentials_path, SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open(token_path, "w") as token:
            token.write(creds.to_json())
    return creds


def fetch_deck(creds: Credentials, document_id: str) -> list[str]:
    try:
        service = build("docs", "v1", credentials=creds)
        # Retrieve the documents contents from the Docs service.
        document = service.documents().get(documentId=document_id).execute()
        contents = [
            d["paragraph"]["elements"][0]["textRun"]["content"]
            for d in document["body"]["content"]
            if "paragraph" in d
        ]
        return contents
    except HttpError as err:
        raise err


def main() -> None:
    """Shows basic usage of the Docs API.
    Prints the title of a sample document.
    """
    document_id = os.getenv("DOCUMENT_ID")
    if document_id is None:
        print("Error: DOCUMENT_ID is not set", file=sys.stderr)
        sys.exit(1)
    credentials_dir = os.getenv(
        "CREDENTIALS_DIR", os.path.join(Path.home(), ".config/mimifuku")
    )
    creds = get_credentials(credentials_dir)
    contents = fetch_deck(creds, document_id)
    deck = MimifukuDeck(contents)
    tts(deck)


if __name__ == "__main__":
    main()
