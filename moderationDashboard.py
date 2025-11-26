import requests
import re
import pandas as pd
import streamlit as st
# --- New Imports for Date Handling ---
from datetime import datetime, date
import pytz
# --------------------------------------------
# STREAMLIT CONFIG
# --------------------------------------------
st.set_page_config(page_title="Facebook Phone Extractor", layout="wide")
st.title("📩 Facebook Inbox Phone Extractor")
st.caption("Extract phone numbers from page inbox")

# --------------------------------------------
# PAGE TOKENS
# --------------------------------------------
PAGES = {
    "Elokabyofficial": "EAAIObOmY9V4BQHn7kMYN7ZA34fW3s5cc1Q1IKm8iLW0YBsjjqTLZC6twmqL7k882e2rpTGCm8cUEg5SYRZA0JVM9dItBcxyVZBu7mkOEi3emuGmtMQkNERlCGlULQc59bEiU5sOmcUrdK4yM744u2TTe1MtFVkZA5ZALdO1rditBcXZA83kIgfbcWQZC9YNHXVw3Aj0ZD",
    "Elokabyالعقبي": "EAAIObOmY9V4BQMxDV7mlEbG5epWvoZC08UYVOtZCV3xvc4UjoqoEGiL2XEmiYDFo1tOPSVZCmUk5Ahmmrg2IzLi7V6qmh5PPzYEqD3RKR7D5YGSlqLDfDN8cNFCkDm5TJAeXFrjd7CN5zO85QANsyuge8vgBfDqNwxKZBPLReNRppZBsDsyFQEZBix7BcxYyTisBeB",
    "ElOkabyBeauty": "EAAIObOmY9V4BQBXRiKmZBfXk41oSPcZBtainPw9CcBdGbCHSeiQVWwDpday88HHKPkJXrv5KQMIhqSW2jxACzBvfbnpuGBY4YOPcmZBIHMoojdR33VTtFSTQKaWVpXaGreZANRrzxGmJry9HGf9YrOY7UtxxjPEV3etMDsYe54RrtA9AAQIEPZBOj55KEm6lFqX71ZANxa",
    "تركيبات دكتور محمد العقبي": "EAAIObOmY9V4BQM6kWztoW74ek1gm4mpvRm4Qx7r92OL7KTwWdqiZC4bGPqGu8yE9mgjO34wSQJeTr3VesUMVP8UZA2dCJuJxSbUH0sE4F3PhJ2X6k0HMYPNYcENp0FBE4kQ0x0yhZC6YyX8mlJ1l8QbH5cIEp3ZB4PkfbpOwZCrYOWxIiAwnR9XqvgC4o7VlFSheG",
    "تركيبات دكتور محمد العقبي للشعر": "EAAIObOmY9V4BQHvhZAzY0bZC7tw5V39846yvhhDI3KJIjwJQit7d8cHjLeIsOZCmWNbmRszjjojcWy1xCImw47GMbuoctaZCKZAmWn7WXuZCKLrKtjhBxcVSr2RHK7IlVrNqr48waJWQ2j4L7mayTJBooQ2pdBlXQe2SBZAqxxwTJ1WZCtVC1E7VxbaJYMZC1aU2i6BtDXguK",
    "صيدليات العقبي Pharmac": "EAAIObOmY9V4BQLue7ExGaTjGypUSLx8BUjHnAYOit91imelbjSL6ZAN7OVfWJSV3KLgEev4tWxAPZCTN2kcxQN8isMqR1S6rUr3bTi0L8shuiCNLYZArZBs1vlgzOS8XmxpSHn4z1iZCp7ZCky8XWjQhNtK8ETpS5x50cosb6iqQZAUmMW7aEJRrmXG42GkxcZCjzbtBpWu2",
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
# GET MESSAGES + EXTRACT
# --------------------------------------------
# Define a Streamlit session state variable to store extracted data across runs
if 'extracted_data' not in st.session_state:
    st.session_state['extracted_data'] = {}

def process_page(token, page_name):
    # 1. Get Today's Date/Time
    # Set the timezone to UTC or another appropriate timezone for accurate filtering.
    # Facebook timestamps are generally UTC.
    UTC = pytz.timezone('UTC')
    today_start = datetime.combine(date.today(), datetime.min.time(), tzinfo=UTC)
    
    # The Graph API accepts a Unix timestamp or an ISO 8601 string (e.g., '2025-11-26T00:00:00+0000')
    # Using Unix timestamp (seconds since epoch) is often simpler and more reliable.
    today_unix_timestamp = int(today_start.timestamp())

    # 2. Filter API Request using 'since' parameter
    # The 'since' parameter on /conversations filters for conversations with messages
    # created on or after the specified time.
    url = (
        f"https://graph.facebook.com/v18.0/me/conversations?"
        f"fields=participants,messages{{message,from,created_time}}&"
        f"since={today_unix_timestamp}&"  # <-- Filter for messages today
        f"access_token={token}"
    )

    all_rows = []
    
    # Load previously extracted data for this page to prevent duplicates
    # A set is used for O(1) average time complexity for lookups.
    page_key = page_name
    if page_key not in st.session_state['extracted_data']:
        st.session_state['extracted_data'][page_key] = set()
    
    previous_extractions = st.session_state['extracted_data'][page_key]

    # Handle Pagination
    while url:
        data = requests.get(url).json()

        for conv in data.get("data", []):
            # Sort messages by created_time descending to get newest first if needed, 
            # though 'since' handles the primary filtering.
            messages = conv.get("messages", {}).get("data", [])
            
            for msg in messages:
                sender = msg.get("from", {}).get("name", "Unknown")
                message = msg.get("message", "")
                created = msg.get("created_time", "")
                
                # Create a unique key for the message to check for duplication
                # Using a combination of timestamp and message content
                unique_key = (created, message) 
                
                if unique_key in previous_extractions:
                    # Skip message if already processed in a previous run
                    continue 

                for phone in extract_phone_numbers(message):
                    # 3. Prevent Duplicates (by adding to set and checking)
                    # Add to all_rows only if it's a new extraction
                    all_rows.append([sender, message, phone, created])
                    
                    # Mark the message as processed in the session state
                    previous_extractions.add(unique_key)
                    
        # Check for the next page of results
        paging = data.get("paging", {})
        url = paging.get("next") if paging.get("next") else None
        
        # Optional: Add a break/limit to prevent endless loops if thousands of messages exist
        # if len(all_rows) > 500: break 

    return all_rows

# --------------------------------------------
# STREAMLIT UI
# --------------------------------------------
# Initialize a DataFrame in session state to hold the cumulative data for display
if 'cumulative_df' not in st.session_state:
    st.session_state['cumulative_df'] = pd.DataFrame(columns=["Sender", "Message", "Phone", "Created", "Page"])

tabs = st.tabs(PAGES.keys())

for i, (page_name, token) in enumerate(PAGES.items()):
    with tabs[i]:
        st.subheader(f"📄 {page_name}")

        if st.button(f"Extract TODAY's messages from {page_name}"):
            st.info("⏳ Fetching today's messages...")

            # Process the page and get *only* the new rows
            new_rows = process_page(token, page_name)

            if not new_rows:
                st.warning("No new phone numbers found today.")
                continue

            # Add the page name to the new rows for the cumulative DataFrame
            new_df = pd.DataFrame(new_rows, columns=["Sender", "Message", "Phone", "Created"])
            new_df['Page'] = page_name
            
            st.success(f"Found {len(new_df)} **new** phone numbers today for **{page_name}**")
            
            # Combine the new DataFrame with the cumulative DataFrame in session state
            st.session_state['cumulative_df'] = pd.concat(
                [st.session_state['cumulative_df'], new_df], ignore_index=True
            ).drop_duplicates(subset=["Message", "Phone", "Created"]).reset_index(drop=True)
            
            # Display only the newly found data for context in the tab
            st.dataframe(new_df)
            
# --- Display Cumulative Data ---
st.markdown("---")
st.header("✨ Cumulative Extracted Data")

if st.session_state['cumulative_df'].empty:
    st.info("Run an extraction from a tab above to see the cumulative data.")
else:
    # Display the full cumulative DataFrame
    st.dataframe(st.session_state['cumulative_df'])
    
    # Optional: Add a download button for the cumulative data
    csv = st.session_state['cumulative_df'].to_csv(index=False).encode('utf-8')
    st.download_button(
        label="⬇️ Download All Extracted Data as CSV",
        data=csv,
        file_name='facebook_phone_numbers_cumulative.csv',
        mime='text/csv',
    )
