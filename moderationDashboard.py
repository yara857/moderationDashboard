import streamlit as st
import requests
import re
import pandas as pd
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

# --------------------------------------------
# PAGE CONFIG
# --------------------------------------------
st.set_page_config(page_title="Facebook Scraper", layout="wide")
st.title("📩 Facebook Inbox Phone Extractor")
st.caption("One tab for each Facebook Page")


# --------------------------------------------
# GOOGLE SHEET CONFIG
# --------------------------------------------
SPREADSHEET_ID = "1sUvzHYfY5RmAs0BPmW3B1tRFWe6ryNXudi1ss0kLJ3g"

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

creds = Credentials.from_service_account_file(
    r"striped-sunspot-451315-t6-343357709c71.json",
    scopes=SCOPES
)
sheets = build("sheets", "v4", credentials=creds).spreadsheets()


# --------------------------------------------
# PAGE ACCESS TOKENS
# --------------------------------------------
PAGES = {
    "Elokabyofficial": "EAAIObOmY9V4BQHn7kMYN7ZA34fW3s5cc1Q1IKm8iLW0YBsjjqTLZC6twmqL7k882e2rpTGCm8cUEg5SYRZA0JVM9dItBcxyVZBu7mkOEi3emuGmtMQkNERlCGlULQc59bEiU5sOmcUrdK4yM744u2TTe1MtFVkZA5ZALdO1rditBcXZA83kIgfbcWQZC9YNHXVw3Aj0ZD",
    "Elokabyالعقبي": "EAAIObOmY9V4BQMxDV7mlEbG5epWvoZC08UYVOtZCV3xvc4UjoqoEGiL2XEmiYDFo1tOPSVZCmUk5Ahmmrg2IzLi7V6qmh5PPzYEqD3RKR7D5YGSlqLDfDN8cNFCkDm5TJAeXFrjd7CN5zO85QANsyuge8vgBfDqNwxKZBPLReNRppZBsDsyFQEZBix7BcxYyTisBeB",
    "ElOkabyBeauty": "EAAIObOmY9V4BQBXRiKmZBfXk41oSPcZBtainPw9CcBdGbCHSeiQVWwDpday88HHKPkJXrv5KQMIhqSW2jxACzBvfbnpuGBY4YOPcmZBIHMoojdR33VTtFSTQKaWVpXaGreZANRrzxGmJry9HGf9YrOY7UtxxjPEV3etMDsYe54RrtA9AAQIEPZBOj55KEm6lFqX71ZANxa",
    "تركيبات دكتور محمد العقبي": "EAAIObOmY9V4BQM6kWztoW74ek1gm4mpvRm4Qx7r92OL7KTwWdqiZC4bGPqGu8yE9mgjO34wSQJeTr3VesUMVP8UZA2dCJuJxSbUH0sE4F3PhJ2X6k0HMYPNYcENp0FBE4kQ0x0yhZC6YyX8mlJ1l8QbH5cIEp3ZB4PkfbpOwZCrYOWxIiAwnR9XqvgC4o7VlFSheG",
    "تركيبات دكتور محمد العقبي للشعر": "EAAIObOmY9V4BQHvhZAzY0bZC7tw5V39846yvhhDI3KJIjwJQit7d8cHjLeIsOZCmWNbmRszjjojcWy1xCImw47GMbuoctaZCKZAmWn7WXuZCKLrKtjhBxcVSr2RHK7IlVrNqr48waJWQ2j4L7mayTJBooQ2pdBlXQe2SBZAqxxwTJ1WZCtVC1E7VxbaJYMZC1aU2i6BtDXguK",
    "صيدليات العقبي Pharmac": "EAAIObOmY9V4BQLue7ExGaTjGypUSLx8BUjHnAYOit91imelbjSL6ZAN7OVfWJSV3KLgEev4tWxAPZCTN2kcxQN8isMqR1S6rUr3bTi0L8shuiCNLYZArZBs1vlgzOS8XmxqSHn4z1iZCp7ZCky8XWjQhNtK8ETpS5x50cosb6iqQZAUmMW7aEJRrmXG42GkxcZCjzbtBpWu2",
    "صيدليات العقبي": "EAAIObOmY9V4BQIZAAHtQY8ZBWufAUAooQ4LHv4li2c7yS63tHTpZCIkR7Ng62FiXBmt88NkIapWoMX6IscHxy8z3ZCEfmzr16x5YBbr7iypDLSvk8fTLhhAYhIokEl2DRUQrld7baDeoAfeZC9Iu0arG4ZAa4QNRP6YgDLvEeZAp7xtipdJICOSiQZBs8PewopzmOmODMsjh",
    "DrElokabyDrPeel": "EAAIObOmY9V4BQAz2ZCFN68D2P63afQG3WHo7tiVO0MDlkeYpICK1PWsXyGmsUhZCvSVoftNu79LeMrDxvMZC9H6qWEaegMPc5O64ZCkbeiaordTYb9PUQvX3bAScrTZA6lQw2oWBTu95rHZA18tbkSYNFqw5ePExmyWuslkiGCTjsBKiW6nUfB9LIcUR4Fn8VGKrQW"
}

# --------------------------------------------
# PHONE REGEX
# --------------------------------------------
english_phone = re.compile(r"\b01[0-9]{9}\b")
arabic_phone = re.compile(r"\b٠١[٠-٩]{9}\b")


def extract_phone_numbers(text):
    if not text:
        return []
    return english_phone.findall(text) + arabic_phone.findall(text)


# --------------------------------------------
# RESET SHEET
# --------------------------------------------
def reset_sheet(sheet_name):
    meta = sheets.get(spreadsheetId=SPREADSHEET_ID).execute()

    for s in meta["sheets"]:
        if s["properties"]["title"] == sheet_name:
            sheets.batchUpdate(
                spreadsheetId=SPREADSHEET_ID,
                body={"requests": [{"deleteSheet": {"sheetId": s["properties"]["sheetId"]}}]}
            ).execute()

    sheets.batchUpdate(
        spreadsheetId=SPREADSHEET_ID,
        body={"requests": [{"addSheet": {"properties": {"title": sheet_name}}}]}
    ).execute()

    sheets.values().update(
        spreadsheetId=SPREADSHEET_ID,
        range=f"{sheet_name}!A1:D1",
        valueInputOption="RAW",
        body={"values": [["Sender", "Message", "Phone", "Created Time"]]}
    ).execute()


# --------------------------------------------
# PROCESS PAGE
# --------------------------------------------
def process_page(page, token):
    url = f"https://graph.facebook.com/v18.0/me/conversations?fields=participants,messages{{message,from,created_time}}&access_token={token}"
    result = requests.get(url).json()

    rows = []
    for conv in result.get("data", []):
        for msg in conv.get("messages", {}).get("data", []):
            sender = msg.get("from", {}).get("name", "Unknown")
            message = msg.get("message", "")
            created = msg.get("created_time", "")
            for phone in extract_phone_numbers(message):
                rows.append([sender, message, phone, created])

    return rows


# --------------------------------------------
# STREAMLIT TABS
# --------------------------------------------
tabs = st.tabs(list(PAGES.keys()))

for idx, (page, token) in enumerate(PAGES.items()):
    with tabs[idx]:
        st.subheader(f"📄 {page}")

        if st.button(f"Run extraction for {page}"):
            st.info("⏳ Processing... Please wait...")

            reset_sheet(page)
            rows = process_page(page, token)

            if rows:
                sheets.values().update(
                    spreadsheetId=SPREADSHEET_ID,
                    range=f"{page}!A2",
                    valueInputOption="RAW",
                    body={"values": rows}
                ).execute()

            st.success(f"Done! Extracted {len(rows)} phone numbers.")
            st.dataframe(pd.DataFrame(rows, columns=["Sender", "Message", "Phone", "Created"]))

