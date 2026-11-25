import os
import streamlit as st

if "token" in st.secrets and not os.path.exists("token.json"):
    with open("token.json", "w") as f:
        f.write(st.secrets["token"])

if "client_secret" in st.secrets and not os.path.exists("client_secret.json"):
    with open("client_secret.json", "w") as f:
        f.write(st.secrets["client_secret"])
import os
import time
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from toxiguard_engine import analyze_and_log

# ==========================================================
# PASTE YOUR YOUTUBE VIDEO ID BELOW
# Example: for https://www.youtube.com/watch?v=abc123XYZ -> "abc123XYZ"
# ==========================================================
VIDEO_ID ="5Zg-4jDPNuI"
CLIENT_SECRETS_FILE = "client_secret.json"
SCOPES = ["https://www.googleapis.com/auth/youtube.force-ssl"]
POLL_INTERVAL = 5


def get_youtube_service():
    if not os.path.exists(CLIENT_SECRETS_FILE):
        print(f"❌ Missing '{CLIENT_SECRETS_FILE}' in ToxiGuard_Project/.")
        print("Download OAuth 2.0 Desktop Client JSON from Google Cloud Console and rename it to client_secret.json.")
        exit(1)

    flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRETS_FILE, SCOPES)
    creds = flow.run_local_server(port=0)
    return build("youtube", "v3", credentials=creds)


def run_youtube_moderator():
    if VIDEO_ID == "PASTE_YOUR_YOUTUBE_VIDEO_ID_HERE":
        print("❌ Paste your YouTube VIDEO_ID into youtube_moderator.py first!")
        exit(1)

    youtube = get_youtube_service()
    seen_ids = set()

    print(f"🎥 ToxiGuard YouTube Live Moderator active on Video ID: {VIDEO_ID}")
    print("Checking for new comments every 5 seconds... (Press CTRL+C to stop)\n")

    while True:
        try:
            response = youtube.commentThreads().list(
                part="snippet",
                videoId=VIDEO_ID,
                textFormat="plainText",
                maxResults=50,
                order="time",
            ).execute()

            for item in response.get("items", []):
                top_comment = item["snippet"]["topLevelComment"]
                comment_id = top_comment["id"]
                if comment_id in seen_ids:
                    continue

                seen_ids.add(comment_id)
                author = top_comment["snippet"]["authorDisplayName"]
                text = top_comment["snippet"]["textDisplay"]

                result = analyze_and_log(
                    text=text,
                    platform=f"YouTube ({VIDEO_ID})",
                    author=author,
                )

                if result["is_toxic"]:
                    # Hides the toxic comment publicly on YouTube immediately
                    youtube.comments().setModerationStatus(
                        id=comment_id,
                        moderationStatus="rejected",
                    ).execute()
                    print(f"🚫 [HIDDEN ON YOUTUBE] {author}: '{text}' -> {result['flagged_categories']}")
                else:
                    print(f"✅ [ALLOWED ON YOUTUBE] {author}: '{text}'")

        except Exception as e:
            print(f"[WARN] YouTube API error: {e}")

        time.sleep(POLL_INTERVAL)


if __name__ == "__main__":
    run_youtube_moderator()