import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
import streamlit as st
import json

service_account_info = dict(st.secrets["firebase"])

# Check if any apps have already been initialized
if not firebase_admin._apps:
    # If no apps have been initialized, initialize the default app
    cred = credentials.Certificate(service_account_info)
    firebase_admin.initialize_app(cred)
else:
    # If an app has already been initialized, use it
    app = firebase_admin.get_app()


db = firestore.client()