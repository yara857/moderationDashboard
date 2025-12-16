import requests
import re
import pandas as pd
import streamlit as st
import os
from datetime import datetime, timedelta

# --------------------------------------------
# CONFIG
# --------------------------------------------
st.set_page_config(page_title="Facebook Phone Extractor", layout="wide")
st.title("📩 Facebook Inbox Phone Extractor")
st.caption("Auto-fetch every 10 minutes + documented CSV history")

CUMULATIVE_FILE = "cumulative_phones.csv"
DOCUMENT_LOG_FILE = "documented_phones_log.csv"

# --------------------------------------------
# PAGE TOKENS
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
# REGEX
# --------------------------------------------
english_phone = re.compile(r"\b01[0-9]{9}\b")
arabic_phone = re.compile(r"\b٠١[٠-٩]{9}\b")

def extract_phone_numbers(text):
    if not text:
        return []
    return english_phone.findall(text) + arabic_phone.findall(text)

# --------------------------------------------
# PRODUCT
# --------------------------------------------
def get_product(page):
    if page == "DrElokabyDrPeel":
        return "cold peeling"
    elif page == "صيدليات العقبي":
        return "نحافه"
    return "شعر"

# --------------------------------------------
# DATA STORAGE
# --------------------------------------------
def load_csv(path, columns):
    if os.path.exists(path):
        return pd.read_csv(path)
    return pd.DataFrame(columns=columns)

def save_csv(df, path):
    df.to_csv(path, index=False, encoding="utf-8-sig")

# --------------------------------------------
# DOCUMENTATION LOG (APPEND ONLY)
# --------------------------------------------
def log_documentation(rows, page_name):
    if not rows:
        return

    log_df = load_csv(
        DOCUMENT_LOG_FILE,
        ["Sender", "Message", "Phone", "Created", "PageName", "Product", "FetchTime"],
    )

    now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")

    new_log = pd.DataFrame(rows, columns=["Sender", "Message", "Phone", "Created"])
    new_log["PageName"] = page_name
    new_log["Product"] = get_product(page_name)
    new_log["FetchTime"] = now

    log_df = pd.concat([log_df, new_log], ignore_index=True)
    save_csv(log_df, DOCUMENT_LOG_FILE)

# --------------------------------------------
# UPDATE CUMULATIVE
# --------------------------------------------
def update_cumulative(rows, page_name):
    df = load_csv(
        CUMULATIVE_FILE,
        ["Sender", "Message", "Phone", "Created", "PageName", "Product", "Status"],
    )

    if not rows:
        return df, 0, 0

    new_df = pd.DataFrame(rows, columns=["Sender", "Message", "Phone", "Created"])
    new_df["PageName"] = page_name
    new_df["Product"] = get_product(page_name)
    new_df["Status"] = "None"

    combined = pd.concat([df, new_df], ignore_index=True)
    deduped = combined.drop_duplicates(subset=["Phone", "PageName"], keep="first")

    new_count = len(deduped) - len(df)
    skipped = len(new_df) - new_count

    save_csv(deduped, CUMULATIVE_FILE)
    return deduped, new_count, skipped

# --------------------------------------------
# FACEBOOK FETCH
# --------------------------------------------
def process_page(token):
    url = f"https://graph.facebook.com/v18.0/me/conversations?fields=messages{{message,from,created_time}}&access_token={token}"
    rows = []

    try:
        data = requests.get(url, timeout=30).json()
    except Exception:
        return rows

    for conv in data.get("data", []):
        for msg in conv.get("messages", {}).get("data", []):
            sender = msg.get("from", {}).get("name", "Unknown")
            message = msg.get("message", "")
            created = msg.get("created_time", "")
            for phone in extract_phone_numbers(message):
                rows.append([sender, message, phone, created])

    return rows

# --------------------------------------------
# SESSION STATE
# --------------------------------------------
if "df" not in st.session_state:
    st.session_state.df = load_csv(
        CUMULATIVE_FILE,
        ["Sender", "Message", "Phone", "Created", "PageName", "Product", "Status"],
    )

if "last_fetch" not in st.session_state:
    st.session_state.last_fetch = None

# --------------------------------------------
# AUTO FETCH (EVERY 10 MIN)
# --------------------------------------------
now = datetime.utcnow()

if (
    st.session_state.last_fetch is None
    or now - st.session_state.last_fetch > timedelta(minutes=10)
):
    total_new = 0
    total_skip = 0

    for page, token in PAGES.items():
        rows = process_page(token)

        # 🔒 DOCUMENT EVERYTHING
        log_documentation(rows, page)

        st.session_state.df, n, s = update_cumulative(rows, page)
        total_new += n
        total_skip += s

    st.session_state.last_fetch = now
    st.toast(f"📁 Documented & fetched | New: {total_new} | Skipped: {total_skip}")

# --------------------------------------------
# MANUAL FETCH
# --------------------------------------------
st.subheader("🔁 Manual Fetch")

tabs = st.tabs(PAGES.keys())

for i, (page, token) in enumerate(PAGES.items()):
    with tabs[i]:
        if st.button(f"Fetch {page}", key=page):
            rows = process_page(token)
            log_documentation(rows, page)
            st.session_state.df, n, s = update_cumulative(rows, page)
            st.success(f"Added {n} | Skipped {s}")

# --------------------------------------------
# STATUS EDIT
# --------------------------------------------
st.subheader("✏️ Update Status")

status_options = [
    "تم التوزيع",
    "تم التأكيد",
    "جاري المتابعة",
    "تم الإلغاء",
    "لا يرد",
    "جاري المحاولة",
    "None",
]

edited = st.data_editor(
    st.session_state.df,
    column_config={
        "Status": st.column_config.SelectboxColumn(
            "Status", options=status_options
        )
    },
    use_container_width=True,
)

st.session_state.df.update(edited)
save_csv(st.session_state.df, CUMULATIVE_FILE)

# --------------------------------------------
# DOWNLOAD
# --------------------------------------------
st.subheader("📥 Download Documented Log")

if os.path.exists(DOCUMENT_LOG_FILE):
    st.download_button(
        "⬇ Download Full Documentation CSV",
        open(DOCUMENT_LOG_FILE, "rb"),
        file_name="documented_phones_log.csv",
        mime="text/csv",
    )
