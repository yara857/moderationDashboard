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
st.title("📩 Facebook Inbox Phone Extractor (Auto every 10 mins)")
st.caption("Automatically fetches Facebook inbox messages and saves unique phone numbers.")

CUMULATIVE_FILE = "cumulative_phones.csv"

# --------------------------------------------
# PAGE TOKENS (REPLACE WITH REAL TOKENS)
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
# DATA STORAGE
# --------------------------------------------
def load_cumulative_data():
    if os.path.exists(CUMULATIVE_FILE):
        return pd.read_csv(CUMULATIVE_FILE)
    return pd.DataFrame(columns=["Sender", "Message", "Phone", "Created", "PageName", "Product", "Status"])

def save_cumulative_data(df):
    df.to_csv(CUMULATIVE_FILE, index=False, encoding="utf-8-sig")

def update_cumulative_data(rows, page_name):
    df = load_cumulative_data()

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

    save_cumulative_data(deduped)
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
# PRODUCT LOGIC
# --------------------------------------------
def get_product(page):
    if page == "DrElokabyDrPeel":
        return "cold peeling"
    elif page == "صيدليات العقبي":
        return "نحافه"
    return "شعر"

# --------------------------------------------
# SESSION STATE
# --------------------------------------------
if "cumulative_df" not in st.session_state:
    st.session_state.cumulative_df = load_cumulative_data()

if "last_fetch" not in st.session_state:
    st.session_state.last_fetch = None

# --------------------------------------------
# AUTO FETCH EVERY 10 MIN
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
        st.session_state.cumulative_df, n, s = update_cumulative_data(rows, page)
        total_new += n
        total_skip += s

    st.session_state.last_fetch = now
    st.toast(f"🔄 Auto fetched | New: {total_new} | Skipped: {total_skip}")

# --------------------------------------------
# MANUAL FETCH
# --------------------------------------------
st.markdown("## 🔁 Manual Fetch")

tabs = st.tabs(PAGES.keys())

for i, (page, token) in enumerate(PAGES.items()):
    with tabs[i]:
        if st.button(f"Fetch {page}", key=page):
            rows = process_page(token)
            st.session_state.cumulative_df, n, s = update_cumulative_data(rows, page)
            st.success(f"Added {n} | Skipped {s}")

# --------------------------------------------
# EDIT STATUS
# --------------------------------------------
st.markdown("## ✏️ Update Status")

df = st.session_state.cumulative_df.copy()

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
    df,
    column_config={
        "Status": st.column_config.SelectboxColumn(
            "Status", options=status_options
        )
    },
    use_container_width=True,
)

df.update(edited)
save_cumulative_data(df)
st.session_state.cumulative_df = df

# --------------------------------------------
# DOWNLOAD
# --------------------------------------------
st.markdown("## 📥 Download Selected")

df_dl = df.copy()
df_dl["Select"] = False

selected = st.data_editor(
    df_dl,
    column_config={"Select": st.column_config.CheckboxColumn()},
    hide_index=False,
    use_container_width=True,
)

out = selected[selected["Select"]].drop(columns=["Select"])

if not out.empty:
    st.download_button(
        "⬇ Download CSV",
        out.to_csv(index=True, encoding="utf-8-sig"),
        "selected_records.csv",
        "text/csv",
    )
else:
    st.warning("No rows selected.")
