import requests
import os
from dotenv import load_dotenv

load_dotenv()

# In production, store the API token in environment variables for security
ZENDESK_API_TOKEN = os.getenv('ZENDESK_API_TOKEN')
ZENDESK_USER_EMAIL = os.getenv('ZENDESK_USER_EMAIL')
ZENDESK_SUBDOMAIN = os.getenv('ZENDESK_SUBDOMAIN')


# Check if ZENDESK_API_TOKEN was correctly retrieved from environment
if not ZENDESK_API_TOKEN:
    print('ZENDESK_API_TOKEN environment variable is not set. Exiting.')
    exit()

auth = f'{ZENDESK_USER_EMAIL}/token', ZENDESK_API_TOKEN

# Function to create a new ticket
def create_ticket(subject, description):
    url = f'https://{ZENDESK_SUBDOMAIN}/api/v2/tickets.json'
    headers = {'Content-Type': 'application/json'}
    data = {
        "ticket": {
            "subject": subject,
            "description": description
        }
    }
    response = requests.post(url, json=data, auth=auth, headers=headers)
    if response.status_code != 201:
        print('Status:', response.status_code, 'Problem with the request. Exiting.')
        exit()
    return response.json()['ticket']['id']

# Function to add a comment to a ticket
def add_agent_comment(ticket_id, comment):
    url = f'https://{ZENDESK_SUBDOMAIN}/api/v2/tickets/{ticket_id}.json'
    headers = {'Content-Type': 'application/json'}
    data = {
        "ticket": {
            "comment": {
                "body": comment
            }
        }
    }
    response = requests.put(url, json=data, auth=auth, headers=headers)
    if response.status_code != 200:
        print('Status:', response.status_code, 'Problem with the request. Exiting.')
        exit()

# Create a new ticket
ticket_id = create_ticket("Test Ticket", "This is a test ticket created via API")

def add_requester_comment(ticket_id, comment, email, name):
    # First, find or create the requester user
    user_search_url = f'https://{ZENDESK_SUBDOMAIN}/api/v2/users/search.json?query={email}'
    user_response = requests.get(user_search_url, auth=auth)
    if user_response.status_code != 200:
        print('Status:', user_response.status_code, 'Problem with the user search request. Exiting.')
        exit()
    users = user_response.json().get('users')
    if users:
        requester_id = users[0]['id']
    else:
        # Create a new user if not found
        user_create_url = f'https://{ZENDESK_SUBDOMAIN}/api/v2/users.json'
        user_data = {
            "user": {
                "name": name,
                "email": email,
                "role": "end-user"
            }
        }
        user_create_response = requests.post(user_create_url, json=user_data, auth=auth)
        if user_create_response.status_code != 201:
            print('Status:', user_create_response.status_code, 'Problem with the user creation request. Exiting.')
            exit()
        requester_id = user_create_response.json()['user']['id']

    # Add the comment as the requester
    url = f'https://{ZENDESK_SUBDOMAIN}/api/v2/tickets/{ticket_id}.json'
    headers = {'Content-Type': 'application/json'}
    data = {
        "ticket": {
            "comment": {
                "body": comment,
                "author_id": requester_id
            },
            "requester_id": requester_id
        }
    }
    response = requests.put(url, json=data, auth=auth, headers=headers)
    if response.status_code != 200:
        print('Status:', response.status_code, 'Problem with the request. Exiting.')
        exit()

# Add a comment to the newly created ticket
add_agent_comment(ticket_id, "This is a test comment added to the ticket")

# Add a comment to the newly created ticket as the requester
add_requester_comment(ticket_id, "This is a test comment added to the ticket by the requester", "john.doe@gmail.com", "John Doe")

# Fetch and print all tickets data
url = f'https://{ZENDESK_SUBDOMAIN}/api/v2/tickets.json'
response = requests.get(url, auth=auth)
if response.status_code != 200:
    print('Status:', response.status_code, 'Problem with the request. Exiting.')
    exit()
data = response.json()
for ticket in data['tickets']:
    print(f"Ticket ID: {ticket['id']} - Subject: {ticket['subject']}")
