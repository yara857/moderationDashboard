import requests
import re
import pandas as pd
import streamlit as st
import os
from datetime import datetime, timedelta
from streamlit_autorefresh import st_autorefresh


# AUTO REFRESH EVERY 10 MINUTES (NATIVE)
# --------------------------------------------
st.experimental_set_query_params(refresh=str(datetime.utcnow()))
st.experimental_rerun()


# --------------------------------------------
# FILE PATH FOR PERSISTENCE
# --------------------------------------------
CUMULATIVE_FILE = "cumulative_phones.csv"

# --------------------------------------------
# STREAMLIT CONFIG
# --------------------------------------------
st.set_page_config(page_title="Facebook Phone Extractor", layout="wide")
st.title("📩 Facebook Inbox Phone Extractor (Auto – Every 10 Minutes)")
st.caption("Automatically fetches inbox messages every 10 minutes and saves new phone numbers.")

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
# DATA PERSISTENCE
# --------------------------------------------
def load_cumulative_data():
    if os.path.exists(CUMULATIVE_FILE):
        return pd.read_csv(CUMULATIVE_FILE)
    return pd.DataFrame(columns=["Sender", "Message", "Phone", "Created", "PageName"])

def save_cumulative_data(df):
    df.to_csv(CUMULATIVE_FILE, index=False, encoding="utf-8-sig")

def update_cumulative_data(new_rows, page_name):
    cumulative_df = load_cumulative_data()

    if not new_rows:
        return cumulative_df, 0, 0

    new_df = pd.DataFrame(new_rows, columns=["Sender", "Message", "Phone", "Created"])
    new_df["PageName"] = page_name

    combined = pd.concat([cumulative_df, new_df], ignore_index=True)
    deduped = combined.drop_duplicates(subset=["Phone", "PageName"], keep="first")

    new_count = len(deduped) - len(cumulative_df)
    skipped = len(new_df) - new_count

    save_cumulative_data(deduped)
    return deduped, new_count, skipped

# --------------------------------------------
# FETCH FACEBOOK MESSAGES
# --------------------------------------------
def process_page(token, page_name):
    url = f"https://graph.facebook.com/v18.0/me/conversations?fields=participants,messages{{message,from,created_time}}&access_token={token}"
    rows = []

    try:
        data = requests.get(url, timeout=30).json()
    except Exception:
        data = {"data": []}

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
if "cumulative_df" not in st.session_state:
    st.session_state.cumulative_df = load_cumulative_data()

if "last_auto_fetch" not in st.session_state:
    st.session_state.last_auto_fetch = None

# --------------------------------------------
# AUTO FETCH ALL PAGES (EVERY 10 MIN)
# --------------------------------------------
def auto_fetch_all_pages():
    now = datetime.utcnow()

    if (
        st.session_state.last_auto_fetch
        and now - st.session_state.last_auto_fetch < timedelta(minutes=10)
    ):
        return

    total_new = 0
    total_skipped = 0

    for page_name, token in PAGES.items():
        new_rows = process_page(token, page_name)
        st.session_state.cumulative_df, new_count, skipped = update_cumulative_data(
            new_rows, page_name
        )
        total_new += new_count
        total_skipped += skipped

    st.session_state.last_auto_fetch = now

    st.toast(
        f"🔄 Auto fetch done | New: {total_new} | Skipped: {total_skipped}",
        icon="✅",
    )

# RUN AUTO FETCH
auto_fetch_all_pages()

# --------------------------------------------
# MANUAL PAGE BUTTONS
# --------------------------------------------
tabs = st.tabs(PAGES.keys())

for i, (page_name, token) in enumerate(PAGES.items()):
    with tabs[i]:
        if st.button(f"Fetch {page_name}", key=f"fetch_{page_name}"):
            rows = process_page(token, page_name)
            st.session_state.cumulative_df, new_count, skipped = update_cumulative_data(
                rows, page_name
            )
            st.success(f"Added {new_count} | Skipped {skipped}")

# --------------------------------------------
# PRODUCT LOGIC
# --------------------------------------------
df = st.session_state.cumulative_df.copy()

def get_product(page):
    if page == "DrElokabyDrPeel":
        return "cold peeling"
    elif page == "صيدليات العقبي":
        return "نحافه"
    return "شعر"

df["Product"] = df["PageName"].apply(get_product)

# --------------------------------------------
# STATUS COLUMN
# --------------------------------------------
status_options = [
    "تم التوزيع",
    "تم التأكيد",
    "جاري المتابعة",
    "تم الإلغاء",
    "لا يرد",
    "جاري المحاولة",
    "None",
]

if "Status" not in df.columns:
    df["Status"] = "None"

# --------------------------------------------
# EDITOR
# --------------------------------------------
st.subheader("✏️ Update Status")

edited_df = st.data_editor(
    df,
    column_config={
        "Status": st.column_config.SelectboxColumn(
            "Status", options=status_options
        )
    },
    use_container_width=True,
)

df.update(edited_df)
save_cumulative_data(df)
st.session_state.cumulative_df = df
st.success("✔ Auto-saved")

# --------------------------------------------
# DOWNLOAD SELECTED
# --------------------------------------------
st.subheader("📥 Download Selected Records")

df_sel = df.copy()
df_sel["Select"] = False

selected = st.data_editor(
    df_sel,
    column_config={"Select": st.column_config.CheckboxColumn()},
    hide_index=False,
    use_container_width=True,
)

download_df = selected[selected["Select"]].drop(columns=["Select"])

if not download_df.empty:
    st.download_button(
        "⬇ Download CSV",
        download_df.to_csv(index=True, encoding="utf-8-sig"),
        "selected_records.csv",
        "text/csv",
    )
else:
    st.warning("No rows selected.")

