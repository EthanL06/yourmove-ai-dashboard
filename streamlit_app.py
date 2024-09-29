from firebase import db
import streamlit as st
from datetime import datetime, date
from subscription_functions import add_product, remove_product, check_subscription, update_subscription, extend_subscription, pull_data, grant_subscription, tag_creator_account
import json 
import pandas as pd
import hmac

def check_password():
    """Returns `True` if the user had the correct password."""

    def password_entered():
        """Checks whether a password entered by the user is correct."""
        if hmac.compare_digest(st.session_state["password"], st.secrets["password"]):
            st.session_state["password_correct"] = True
            del st.session_state["password"]  # Don't store the password.
        else:
            st.session_state["password_correct"] = False

    # Return True if the password is validated.
    if st.session_state.get("password_correct", False):
        return True

    st.title("Access Admin Dashboard:")
    # Show input for password.
    st.text_input(
        "Password", type="password", on_change=password_entered, key="password"
    ) 
    st.caption("Press Enter to submit the password.")

    if "password_correct" in st.session_state:
        st.error("😕 Password incorrect")
    return False

if not check_password():
    st.stop()

tab1, tab2 = st.tabs(["Access", "Chargeback"])

with tab1:
    st.info("Test it out with the email thanks@yourmove.ai")
    st.header("Add Product to User")
    email = st.text_input("User Email")
    product = st.selectbox(
        "Select Product", ["profile_writer", "profile_review", "ai_photos"])

    if st.button("Add Product"):
        result = add_product(email, product)

        if result:
            st.success(f"Product '{product}' added to user '{email}'.")
        else:
            st.error(f"Product '{product}' already exists for user '{email}'.")

    st.header("Remove Product from User")
    remove_email = st.text_input(label="User Email", key="remove_email")
    remove_selected_product = st.selectbox(
        label="Select Product", options=["profile_writer", "profile_review", "ai_photos"], key="remove_product")

    if st.button("Remove Product"):
        result = remove_product(remove_email, remove_selected_product)

        if result:
            st.success(
                f"Product '{remove_selected_product}' removed from user '{remove_email}'.")
        else:
            st.error(
                f"Product '{remove_selected_product}' not found for user '{remove_email}'.")

    st.header("Check User Subscription")
    check_email = st.text_input("Email to Check Subscription")
    if st.button("Check Subscription"):
        is_subscribed = check_subscription(check_email)
        if is_subscribed:
            st.success(f"User '{check_email}' is Subscribed.")
        else:
            st.error(f"User '{check_email}' is Not Subscribed.")

    # st.header("Update User Subscription")
    # update_email = st.text_input("Email to Update Subscription")
    # update_status = st.selectbox("Subscription Status", [True, False])
    # update_expiry = st.date_input("Subscription expiry", disabled=(not update_status), min_value=(datetime.today()))
    
    # if st.button("Update Subscription"):
    #     result = update_subscription(update_email, update_status, update_expiry if update_status else None)

    #     if result:
    #         st.success(
    #             f"User '{update_email}' subscription status updated to: {update_status}")
    #     else:
    #         st.error(f"User '{update_email}' not found.")

    st.header("Extend User Subscription")
    extend_email = st.text_input("Email to Extend Subscription")
    additional_time = st.number_input(
        "Additional Time (days)", min_value=1, max_value=100000, step=1)

    if st.button("Extend Subscription"):
        result = extend_subscription(extend_email, additional_time)

        if result['success']:
            st.success(result['message'])
        else:
            st.error(result['message'])

    st.header("Grant User Subscription")
    grant_email = st.text_input("Email to Grant Subscription", key="grant_email")
    grant_time = st.number_input(
        "Access Time (days)", min_value=1, max_value=100000, step=1, key="grant_time")

    if st.button("Grant Subscription"):
        result = grant_subscription(grant_email, grant_time)

        if result['success']:
            st.success(result['message'])
        else:
            st.error(result['message'])

    st.header("Tag Creator Account")
    creator_email = st.text_input("Email to Tag as Creator", key="creator_email")

    if st.button("Tag as Creator"):
        result = tag_creator_account(creator_email)

        if result['success']:
            st.success(result['message'])
        else:
            st.error(result['message'])

with tab2:
    st.info("Test it out with the email thanks@yourmove.ai")
    st.header("Pull Data from Firebase")
    email = st.text_input(label="User Email", key="chargeback_email")
    if st.button("Go"):
        with st.spinner('Pulling data...'):
            data = pull_data(email)

        st.subheader(f"Data for {email}:")
        with st.expander('Refreshes'):
            st.dataframe(data['refreshes'])
        
        with st.expander('Requests (json only)'):
            st.json(data['requests'])

        with st.expander('Profiles'):
            df = pd.DataFrame(data['profiles'])
        
            if 'generatedProfile' in df.columns:
                # Convert each object in the 'generatedProfiles' column to a JSON string
                
                df['generatedProfile'] = df['generatedProfile'].apply(lambda x: json.dumps(x, indent=2))

            st.dataframe(df)

        with st.expander('Profile Reviews'):
            st.dataframe(data['profileReviews'])
        
        
            