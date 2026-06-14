from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = ["https://www.googleapis.com/auth/drive.file"]

flow = InstalledAppFlow.from_client_secrets_file(
    "credentials.json",
    SCOPES
)

creds = flow.run_local_server(port=0)

with open("token.json", "w") as token:
    token.write(creds.to_json())

service = build("drive", "v3", credentials=creds)

about = service.about().get(fields="user").execute()

print("Login Successful")
print("User:", about["user"]["emailAddress"])
print("token.json created")