from datetime import datetime, timezone, timedelta
from firebase import db
from google.cloud import firestore as firestore_client
from datetime import datetime, timedelta

def add_product(email, product):
    """Add a product to the purchasedProducts collection."""
    try:
        # Query for existing document with the same email and product
        existing_docs = db.collection('purchasedProducts').where(
            'email', '==', email).where('product', '==', product).get()

        if existing_docs:
            print(f"A document with email {email} and product {product} already exists.")
            return False

        doc_ref = db.collection('purchasedProducts').document()

        current_time = datetime.now(timezone.utc)
        formatted_time = current_time.isoformat()

        doc = {
            'createdAt': formatted_time,
            'email': email,
            'product': product,
            'stripe_id': None,
            'updatedAt': formatted_time
        }

        doc_ref.set(doc)
        print(f"Document with email {email} and product {product} added.")
        return True
    except Exception as e:
        print(f"Failed to add document for email {email} and product {product}. Error: {e}")
        return False

def remove_product(email, product):
    """Remove a product from the purchasedProducts collection."""
    try:
        # Query for existing documents with the same email and product
        existing_docs = db.collection('purchasedProducts').where(
            'email', '==', email).where('product', '==', product).get()

        if not existing_docs:
            print(f"No document found with email {email} and product {product} for deletion.")
            return False

        # Initialize a batch operation
        batch = db.batch()

        for doc in existing_docs:
            doc_ref = db.collection('purchasedProducts').document(doc.id)
            batch.delete(doc_ref)

        # Commit the batch operation
        batch.commit()
        print(f"Documents with email {email} and product {product} deleted.")
        return True
    except Exception as e:
        print(f"Failed to delete documents with email {email} and product {product}. Error: {e}")
        return False

def check_subscription(email):
    """Check if a user is subscribed."""
    try:
        user_ref = db.collection('produsers').where('email', '==', email)
        users = user_ref.get()

        if users:
            for user in users:
                if 'isSubscribed' in user.to_dict():
                    return user.to_dict()['isSubscribed']
        return False  
    except Exception as e:
        print(f"Error checking subscription for {email}: {e}")
        return False  


def update_subscription(email, is_subscribed, subscription_expiry):
    """Update a user's subscription status."""
    users_ref = db.collection('produsers').where('email', '==', email)
    docs = users_ref.get()
    
    if not docs:
        print(f"User with email {email} not found.")
        return False

    for doc in docs:
        if doc.exists:
            doc_ref = db.collection('produsers').document(doc.id)
            current_time = datetime.now(timezone.utc)
            formatted_updated_time = current_time.strftime("%Y-%m-%dT%H:%M:%S.%fZ")

            try:
                # Create the update data dictionary
                update_data = {
                    'isSubscribed': is_subscribed,
                    'updatedAt': formatted_updated_time
                }

                # Add subscriptionExpiry only if it's not None
                if subscription_expiry is not None:
                    update_data['subscriptionExpiry'] = subscription_expiry.strftime("%Y-%m-%dT%H:%M:%S.%fZ")
                # Update the document with the constructed dictionary
                doc_ref.update(update_data)
                              
                print(f"Subscription status updated for user with email {email}.")
                return True
            except Exception as e:
                print(f"Failed to update subscription status for user with email {email}. Error: {e}")
                return False
        else:
            print(f"User with email {email} not found.")
            return False

def extend_subscription(email, additional_time):
    """Extend a user's subscription."""
    user_ref = db.collection('produsers').where('email', '==', email)
    docs = user_ref.get()
    
    if not docs:
        print(f"User with email {email} not found.")
        return {
            'success': False,
            'message': f"User with email {email} not found."
        }
    
    for doc in docs:
        if doc.exists:
            doc_ref = db.collection('produsers').document(doc.id)
            current_subscription_expiry = doc_ref.get().to_dict().get('subscriptionExpiry')

            if current_subscription_expiry is None:
                print(f"User with email {email} does not have a subscription expiry date.")
                return {
                    'success': False,
                    'message': f"User with email {email} does not have a subscription expiry date."
                }

            date = None
            if isinstance(current_subscription_expiry, int):
                timestamp_in_seconds = current_subscription_expiry / 1000
                date = datetime.fromtimestamp(timestamp_in_seconds)
            else:
                date = datetime.fromtimestamp(current_subscription_expiry.timestamp())

            # Additional time is a number in days
            additional_time_to_seconds = additional_time * 86400;
            new_subscription_expiry = date + timedelta(seconds=additional_time_to_seconds)

            print(f"Current subscription expiry: {date}")
            print(f"New subscription expiry: {new_subscription_expiry}")

            # Convert date to timestamp
            try:
                doc_ref.update({
                    'subscriptionExpiry': new_subscription_expiry
                })
                return {
                    'success': True,
                    'message': f"Subscription extended for user with email {email} from {date} to {new_subscription_expiry}"
                }
            except Exception as e:
                return {
                    'success': False,
                    'message': f"Failed to extend subscription for user with email {email}. Error: {e}"
                }


def grant_subscription(email, access_time):
    """Grant or extend a user's subscription."""
    user_ref = db.collection('produsers').where('email', '==', email)
    docs = user_ref.get()
    
    if not docs:
        return {
            'success': False,
            'message': f"User with email {email} not found."
        }
    
    for doc in docs:
        if doc.exists:
            doc_ref = db.collection('produsers').document(doc.id)
            current_time = datetime.now(timezone.utc)
            current_subscription_expiry = doc_ref.get().to_dict().get('subscriptionExpiry')

            if current_subscription_expiry:
                if isinstance(current_subscription_expiry, int):
                    expiry_date = datetime.fromtimestamp(current_subscription_expiry / 1000, tz=timezone.utc)
                else:
                    expiry_date = current_subscription_expiry.replace(tzinfo=timezone.utc)
                
                if expiry_date > current_time:
                    new_expiry_date = expiry_date + timedelta(days=access_time)
                else:
                    new_expiry_date = current_time + timedelta(days=access_time)
            else:
                new_expiry_date = current_time + timedelta(days=access_time)

            try:
                doc_ref.update({
                    'isSubscribed': True,
                    'subscriptionExpiry': new_expiry_date,
                    'updatedAt': current_time.isoformat()
                })
                return {
                    'success': True,
                    'message': f"Subscription granted/extended for user with email {email}. New expiry date: {new_expiry_date.isoformat()}"
                }
            except Exception as e:
                return {
                    'success': False,
                    'message': f"Failed to grant/extend subscription for user with email {email}. Error: {e}"
                }

    return {
        'success': False,
        'message': f"User with email {email} not found."
    }
    
def pull_data(email):
    data = {
        'refreshes': [],
        'requests': [],
        'profiles': [],
        'profileReviews': [],
    }

    # Fetch and process refreshes
    refreshes_query = db.collection('refreshes').where('email', '==', email).get()
    data['refreshes'] = [doc.to_dict() for doc in refreshes_query]

    # Fetch and process requests
    requests_query = db.collection('requests').where('email', '==', email).get()
    data['requests'] = [doc.to_dict() for doc in requests_query]

    # Fetch and process profiles
    profiles_query = db.collection('profiles').where('email', '==', email).get()
    data['profiles'] = [doc.to_dict() for doc in profiles_query]

    # Fetch and process profileReviews
    profileReviews_query = db.collection('profileReviews').where('email', '==', email).get()
    data['profileReviews'] = [doc.to_dict() for doc in profileReviews_query]

    return data

def tag_creator_account(email):
    """
    Tag an account as a creator, grant a 365-day subscription, and set isCreator to True.
    """
    # First, grant a 365-day subscription
    grant_result = grant_subscription(email, 365)
    
    if not grant_result['success']:
        return grant_result  # Return the error if granting subscription failed
    
    # If subscription was granted successfully, update isCreator field
    user_ref = db.collection('produsers').where('email', '==', email)
    docs = user_ref.get()
    
    if not docs:
        return {
            'success': False,
            'message': f"User with email {email} not found."
        }
    
    for doc in docs:
        if doc.exists:
            doc_ref = db.collection('produsers').document(doc.id)
            current_time = datetime.now(timezone.utc)
            
            try:
                doc_ref.update({
                    'isCreator': True,
                    'updatedAt': current_time.isoformat()
                })
                return {
                    'success': True,
                    'message': f"Account {email} tagged as creator and granted 365-day subscription. {grant_result['message']}"
                }
            except Exception as e:
                return {
                    'success': False,
                    'message': f"Failed to tag account {email} as creator. Subscription was granted but creator status update failed. Error: {e}"
                }
    
    return {
        'success': False,
        'message': f"User with email {email} not found after granting subscription. This should not happen."
    }

