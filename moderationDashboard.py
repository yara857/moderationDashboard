import requests
import re
import pandas as pd
import streamlit as st
import os

# --- FILE PATH FOR PERSISTENCE ---
# In a real-world Streamlit deployment, this file would need to be stored
# in a persistent location (like an S3 bucket or a mounted volume).
# For this demonstration, we'll use a file path that assumes local storage access.
CUMULATIVE_FILE = 'cumulative_phones.csv'

# --------------------------------------------
# STREAMLIT CONFIG
# --------------------------------------------
st.set_page_config(page_title="Facebook Phone Extractor", layout="wide")
st.title("📩 Facebook Inbox Phone Extractor (Cumulative)")
st.caption("Extracts phone numbers from page inbox and saves new, unique entries.")

# --------------------------------------------
# PAGE TOKENS (Using tokens from your original code)
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
    """Extracts both English and Arabic format phone numbers."""
    if not text:
        return []
    return english_phone.findall(text) + arabic_phone.findall(text)

# --------------------------------------------
# DATA PERSISTENCE FUNCTIONS
# --------------------------------------------
def load_cumulative_data():
    """Loads the cumulative phone data from the CSV file."""
    if os.path.exists(CUMULATIVE_FILE):
        return pd.read_csv(CUMULATIVE_FILE)
    # Create an empty DataFrame if the file doesn't exist
    return pd.DataFrame(columns=["Sender", "Message", "Phone", "Created", "PageName"])

def save_cumulative_data(df):
    """Saves the cumulative phone data to the CSV file."""
    df.to_csv(CUMULATIVE_FILE, index=False)

def update_cumulative_data(new_rows, page_name):
    """
    Checks for duplicates against existing data and adds only new, unique records.
    """
    cumulative_df = load_cumulative_data()
    
    # 1. Convert new data to DataFrame
    if not new_rows:
        return cumulative_df, 0, 0
    
    new_df = pd.DataFrame(new_rows, columns=["Sender", "Message", "Phone", "Created"])
    new_df['PageName'] = page_name

    # 2. Check for duplicates (Phone number and Page must be unique together)
    # We concatenate to find which rows are duplicates when considering both 'Phone' and 'PageName'
    combined_df = pd.concat([cumulative_df, new_df], ignore_index=True)
    
    # Keep only the first occurrence (which means keeping existing and new unique records)
    deduplicated_df = combined_df.drop_duplicates(subset=['Phone', 'PageName'], keep='first')
    
    # Identify the actual new rows that were added
    newly_added_df = pd.merge(deduplicated_df, cumulative_df, 
                              on=['Phone', 'PageName'], 
                              how='left', 
                              indicator=True)
    
    # Rows where indicator is 'left_only' are the new rows
    newly_added_count = len(newly_added_df[newly_added_df['_merge'] == 'left_only'])
    
    # Calculate skipped duplicates
    duplicates_skipped = len(new_df) - newly_added_count
    
    # 3. Save and return the final DataFrame
    save_cumulative_data(deduplicated_df)
    
    return deduplicated_df, newly_added_count, duplicates_skipped

# --------------------------------------------
# GET MESSAGES + EXTRACT (from your original code)
# --------------------------------------------
# NOTE: The Facebook API call must be executed securely on a backend server 
# in a production environment. Running this directly in Streamlit client-side 
# is highly insecure. This function is maintained to match your original structure.
def process_page(token, page_name):
    """Fetches messages (simulated or real) and extracts phone numbers."""
    url = f"https://graph.facebook.com/v18.0/me/conversations?fields=participants,messages{{message,from,created_time}}&access_token={token}"
    
    try:
        data = requests.get(url).json()
    except requests.exceptions.RequestException as e:
        # Since we cannot run live requests here, we'll provide a mock fallback
        # in a real app, this should handle network errors.
        st.error(f"Network error or Graph API call failed. Using mock data for demonstration. Error: {e}")
        # MOCK DATA FOR DEMO if API fails
        if page_name == "Elokabyofficial":
            data = {
                "data": [{
                    "messages": {"data": [
                        {"from": {"name": "Ahmed Mock"}, "message": "My new phone is 01012345678.", "created_time": "2025-11-25T10:00:00Z"},
                        {"from": {"name": "Sami Mock"}, "message": "٠١٢٩٨٧٦٥٤٣٢ is my contact.", "created_time": "2025-11-25T11:00:00Z"},
                        {"from": {"name": "Duplicate Mock"}, "message": "Call me on 01012345678.", "created_time": "2025-11-25T12:00:00Z"},
                    ]}
                }]
            }
        else:
            data = {"data": []} # No mock data for other pages

    rows = []
    for conv in data.get("data", []):
        for msg in conv.get("messages", {}).get("data", []):
            sender = msg.get("from", {}).get("name", "Unknown")
            message = msg.get("message", "")
            created = msg.get("created_time", "")
            for phone in extract_phone_numbers(message):
                rows.append([sender, message, phone, created])

    return rows

# --------------------------------------------
# STREAMLIT UI LOGIC
# --------------------------------------------
# Initialize session state for the cumulative DataFrame
if 'cumulative_df' not in st.session_state:
    st.session_state.cumulative_df = load_cumulative_data()

# Create tabs for each page
tabs = st.tabs(PAGES.keys())

for i, (page_name, token) in enumerate(PAGES.items()):
    with tabs[i]:
        st.subheader(f"📄 {page_name}")
        
        # Use a unique key for the button to prevent Streamlit warnings
        if st.button(f"Extract and Update Cumulative Data from {page_name}", key=f"extract_{page_name}"):
            with st.spinner(f"⏳ Fetching messages and checking against {CUMULATIVE_FILE}..."):
                
                # 1. Extract new rows from the API
                new_rows = process_page(token, page_name)

                if not new_rows:
                    st.warning("No phone numbers found in the latest fetch.")
                    
                # 2. Update the cumulative data, handle duplicates, and save
                st.session_state.cumulative_df, new_count, skipped_count = update_cumulative_data(new_rows, page_name)

                # 3. Display results of the update
                if new_count > 0:
                    st.success(f"✅ Found {len(new_rows)} messages. Added **{new_count}** new, unique phone numbers from **{page_name}**. Skipped {skipped_count} duplicates.")
                elif len(new_rows) > 0 and new_count == 0:
                    st.info(f"Found {len(new_rows)} messages, but all were duplicates. Total unique records unchanged.")
# --- GLOBAL CUMULATIVE DISPLAY ---
st.markdown("---")
st.header("🌎 Global Cumulative Extracted Phone Numbers")
st.info(f"Total Unique Records: **{len(st.session_state.cumulative_df)}**")

df = st.session_state.cumulative_df.copy()

# ------------------------------------------------------------
# Add Product Column
# ------------------------------------------------------------
def get_product(page):
    if page == "DrElokabyDrPeel":
        return "cold peeling"
    elif page == "صيدليات العقبي":
        return "نحافه"
    else:
        return "شعر"

if "Product" not in df.columns:
    df["Product"] = df["PageName"].apply(get_product)

# ------------------------------------------------------------
# Status Column - RESET to None for all rows
# ------------------------------------------------------------
if "Status" not in df.columns:
    df["Status"] = "None"
else:
    df["Status"] = "None"

st.write("### ✏️ Update Status")

editable_df = df[["Phone", "PageName", "Product", "Sender", "Created", "Message", "Status"]]

edited_df = st.data_editor(
    editable_df,
    use_container_width=True,
    column_config={
        "Status": st.column_config.SelectboxColumn(
            "Status",
            options=[
                "تم التوزيع",
                "تم التأكيد",
                "جاري المتابعة",
                "تم الإلغاء",
                "لا يرد",
                "جاري المحاولة",
                "None"
            ],
        )
    },
    key="editor",
)

df.update(edited_df)
st.session_state.cumulative_df = df

# Save as Excel instead of CSV
excel_path = "cumulative_phones.xlsx"
df.to_excel(excel_path, index=False)

st.success("✔ Status updated and saved!")

# ------------------------------------------------------------
# TABLE FOR SELECTING ROWS TO DOWNLOAD (with Index)
# ------------------------------------------------------------
st.write("### 📥 Select Records to Download")

df_selection = df.copy()
df_selection["Select"] = False

selected_df = st.data_editor(
    df_selection,
    key="selector",
    hide_index=False,
    column_config={
        "Select": st.column_config.CheckboxColumn("Select")
    },
    use_container_width=True,
)

download_data = selected_df[selected_df["Select"] == True].drop(columns=["Select"])

if not download_data.empty:
    # Save selected rows to Excel
    from io import BytesIO
    import openpyxl

    buffer = BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        download_data.to_excel(writer, index=True, sheet_name="Selected")

    st.download_button(
        label="⬇ Download Selected Records (Excel)",
        data=buffer.getvalue(),
        file_name="selected_records.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
else:
    st.warning("No records selected for download.")
