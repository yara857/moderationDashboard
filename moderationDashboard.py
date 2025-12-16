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
    "Elokabyofficial": "TOKEN_1",
    "Elokabyالعقبي": "TOKEN_2",
    "ElOkabyBeauty": "TOKEN_3",
    "تركيبات دكتور محمد العقبي": "TOKEN_4",
    "تركيبات دكتور محمد العقبي للشعر": "TOKEN_5",
    "صيدليات العقبي Pharmac": "TOKEN_6",
    "صيدليات العقبي": "TOKEN_7",
    "DrElokabyDrPeel": "TOKEN_8",
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
