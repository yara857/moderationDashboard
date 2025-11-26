import requests
import re
import pandas as pd
import streamlit as st
from datetime import datetime, date, timedelta
import pytz

# --------------------------------------------
# STREAMLIT CONFIG
# --------------------------------------------
st.set_page_config(page_title="Facebook Phone Extractor", layout="wide")
st.title("📩 Facebook Inbox Phone Extractor")
st.caption("Extract phone numbers from page inbox (Last 24 Hours Only)")

# --------------------------------------------
# PAGE TOKENS (Replace these with your current, valid tokens)
# --------------------------------------------
PAGES = {
    "Elokabyofficial": "EAAIObOmY9V4BQHn7kMYN7ZA34fW3s5cc1Q1IKm8iLW0YBsjjqTLZC6twmqL7k882e2rpTGCm8cUEg5SYRZA0JVM9dItBcxyVZBu7mkOEi3emuGmtMQkNERlCGlULQc59bEiU5sOmcUrdK4yM744u2TTe1MtFVkZA5ZALdO1rditBcXZA83kIgfbcWQZC9YNHXVw3Aj0ZD",
    "Elokabyالعقبي": "EAAIObOmY9V4BQMxDV7mlEbG5epVvoZC08UYVOtZCV3xvc4UjoqoEGiL2XEmiYDFo1tOPSVZCmUk5Ahmmrg2IzLi7V6qmh5PPzYEqD3RKR7D5YGSlqLDfDN8cNFCkDm5TJAeXFrjd7CN5zO85QANsyuge8vgBfDqNwxKZBPLReNRppZBsDsyFQEZBix7BcxYyTisBeB",
    "ElOkabyBeauty": "EAAIObOmY9V4BQBXRiKmZBfXk41oSPcZBtainPw9CcBdGbCHSeiQVWwDpday88HHKPkJXrv5KQMIhqSW2jxACzBvfbnpuGBY4YOPcmZBIHMoojdR33VTtFSTQKaWVpXaGreZANRrzxGmJry9HGf9YrOY7UtxxjPEV3etMDsYe54RrtA9AAQIEPZBOj55KEm6lFqX71ZANxa",
    "تركيبات دكتور محمد العقبي": "EAAIObOmY9V4BQM6kWztoW74ek1gm4mpvRm4Qx7r92OL7KTwWdqiZC4bGPuGu8yE9mgjO34wSQJeTr3VesUMVP8UZA2dCJuJxSbUH0sE4F3PhJ2X6k0HMYPNYcENp0FBE4kQ0x0yhZC6YyX8mlJ1l8QbH5cIEp3ZB4PkfbpOwZCrYOWxIiAwnR9XqvgC4o7VlFSheG",
    "تركيبات دكتور محمد العقبي للشعر": "EAAIObOmY9V4BQHvhZAzY0bZC7tw5V39846yvhhDI3KJIjwJQit7d8cHjLeIsOZCmWNbmRszjjojcWy1xCImw47GMbuoctaZCKZAmWn7WXuZCKLrKtjhBxcVSr2RHK7IlVrNqr48waJWQ2j4L7mayTJBooQ2pdBlXQe2SBZAqxxwTJ1WZCtVC1E7VxbaJYMZC1aU2i6BtDXguK",
    "صيدليات العقبي Pharmac": "EAAIObOmY9V4BQLue7ExGaTjGypUSLx8BUjHnAYOit91imelbjSL6ZAN7OVfWJSV3KLgEev4tWxAPZCTN2kcxQN8isMqR1S6rUr3bTi0L8shuiCNLYZArZBs1vlgzOS8XmxpSHn4z1iZCp7ZCky8XWjQhNtK8ETpS5x50cosb6iqQZAUmMW7aEJRrmXG42GkxcZCjzbtBpWu2",
    "صيدليات العقبي": "EAAIObOmY9V4BQIZAAHtQY8ZBWufAUAooQ4LHv4li2c7yS63tHTpZCIkR7Ng62FiXBmt88NkIapWoMX6IscHxy8z3ZCEfmzr16x5YBbr7iypDLSvk8fTLhhAYhIokEl2DRUQrld7baDeoAfeZC9Iu0arG4ZAa4QNRP6YgDLvEeZAp7xtipdJICOSiQZBs8PewopzmOmODMsjh",
    "DrElokabyDrPeel": "EAAIObOmY9V4BQAz2ZCFN68D2P63afQG3WHo7tiVO0MDlkeYpICK1PWsXyGmsUhZCvSVoftNu79LeMrDxvMZC9H6qWEaegMPc5O64ZCkbeiaordTYb9PUQvX3bAScrTZA6lQw2oWBTu95rHZA18tbkSYNFqw5ePExmyWuslkiGCTjsBKiW6nUfB9LIcUR4Fn8VGKrQW"
}

# --------------------------------------------
# REGEX
# --------------------------------------------
# Matches Egyptian phone numbers starting with 01 followed by 9 digits
english_phone = re.compile(r"\b01[0-9]{9}\b")
# Matches Egyptian phone numbers using Arabic numerals (٠١ followed by 9 digits)
arabic_phone = re.compile(r"\b٠١[٠-٩]{9}\b")

def extract_phone_numbers(text):
    if not text:
        return []
    # Find all matches for both English and Arabic patterns
    return english_phone.findall(text) + arabic_phone.findall(text)

# --------------------------------------------
# SESSION STATE INITIALIZATION
# Used to store data between button clicks to prevent duplicates and maintain history.
# --------------------------------------------
if 'extracted_data' not in st.session_state:
    # Stores unique message keys (created_time, message content) for duplicate prevention
    st.session_state['extracted_data'] = {} 
if 'cumulative_df' not in st.session_state:
    # Stores the final DataFrame containing all unique extractions across all pages/runs
    st.session_state['cumulative_df'] = pd.DataFrame(columns=["Sender", "Message", "Phone", "Created", "Page"])

# --------------------------------------------
# CORE LOGIC: GET MESSAGES + EXTRACT
# --------------------------------------------
def process_page(token, page_name):
    # Set the timezone to UTC for reliable timestamp calculation
    UTC = pytz.timezone('UTC')
    now = datetime.now(UTC)
    
    # Calculate the Unix timestamp for 24 hours ago
    last_24_hours = now - timedelta(hours=24)
    last_24_hours_unix_timestamp = int(last_24_hours.timestamp())

    # CONVERSATION URL: Fetches data since 24 hours ago, with limits for speed.
    # limit=20: Max 20 most recently active conversations.
    # messages.limit(5): Max 5 most recent messages within each conversation.
    url = (
        f"https://graph.facebook.com/v18.0/me/conversations?limit=20&" 
        f"fields=participants,messages.limit(5){{message,from,created_time}}&"
        f"since={last_24_hours_unix_timestamp}&"
        f"access_token={token}"
    )

    all_rows = []
    
    page_key = page_name
    # Initialize the set for this page if it doesn't exist
    if page_key not in st.session_state['extracted_data']:
        st.session_state['extracted_data'][page_key] = set()
    
    previous_extractions = st.session_state['extracted_data'][page_key]

    # Handle Pagination (for conversations)
    while url:
        try:
            data = requests.get(url).json()

            # Check for API errors
            if data.get("error"):
                st.error(f"API Error for {page_name}: {data['error']['message']}")
                return []

            for conv in data.get("data", []):
                messages = conv.get("messages", {}).get("data", [])
                
                for msg in messages:
                    sender = msg.get("from", {}).get("name", "Unknown")
                    message = msg.get("message", "")
                    created = msg.get("created_time", "")
                    
                    # Key for duplicate check: (timestamp, message content)
                    unique_key = (created, message) 
                    
                    if unique_key in previous_extractions:
                        continue 

                    for phone in extract_phone_numbers(message):
                        # Store the data row
                        all_rows.append([sender, message, phone, created])
                        # Mark this message as processed
                        previous_extractions.add(unique_key)
                        
            # Check for the next page of conversations
            paging = data.get("paging", {})
            url = paging.get("next") if paging.get("next") else None
            
            if url is None:
                break 
                
        except requests.exceptions.RequestException as e:
            st.error(f"Network error during API call for {page_name}: {e}")
            break

    return all_rows

# --------------------------------------------
# STREAMLIT UI
# --------------------------------------------
tabs = st.tabs(PAGES.keys())

for i, (page_name, token) in enumerate(PAGES.items()):
    with tabs[i]:
        st.subheader(f"📄 {page_name}")

        if st.button(f"Extract Last 24 Hours Messages from {page_name}"):
            st.info("⏳ Fetching messages...")

            new_rows = process_page(token, page_name)

            if not new_rows:
                st.warning(f"No new phone numbers found in the last 24 hours for {page_name}.")
                continue

            new_df = pd.DataFrame(new_rows, columns=["Sender", "Message", "Phone", "Created"])
            new_df['Page'] = page_name
            
            st.success(f"Found {len(new_df)} **new** phone numbers in the last 24 hours for **{page_name}**")
            
            # Combine the new data with the cumulative data, dropping any duplicates
            st.session_state['cumulative_df'] = pd.concat(
                [st.session_state['cumulative_df'], new_df], ignore_index=True
            ).drop_duplicates(subset=["Message", "Phone", "Created"]).reset_index(drop=True)
            
            # Display only the newly found data in the current tab
            st.dataframe(new_df)
            
# --------------------------------------------
# CUMULATIVE DATA DISPLAY AND DOWNLOAD
# --------------------------------------------
st.markdown("---")
st.header("✨ Cumulative Extracted Data")

if st.session_state['cumulative_df'].empty:
    st.info("Run an extraction from a tab above to see the cumulative data.")
else:
    # Display the full cumulative DataFrame
    st.dataframe(st.session_state['cumulative_df'])
    
    # Download button
    csv = st.session_state['cumulative_df'].to_csv(index=False).encode('utf-8')
    st.download_button(
        label="⬇️ Download All Extracted Data as CSV",
        data=csv,
        file_name='facebook_phone_numbers_cumulative.csv',
        mime='text/csv',
    )
