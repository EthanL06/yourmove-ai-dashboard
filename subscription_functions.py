from datetime import datetime, timezone, timedelta
from firebase import db



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


def update_subscription(email, is_subscribed):
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
                doc_ref.update({
                    'isSubscribed': is_subscribed,
                    'updatedAt': formatted_updated_time
                })
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