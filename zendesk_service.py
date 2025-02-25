import requests
import os
from dotenv import load_dotenv

class ZendeskService:
    def __init__(self):
        load_dotenv()
        self.api_token = os.getenv('ZENDESK_API_TOKEN')
        self.user_email = os.getenv('ZENDESK_USER_EMAIL')
        self.subdomain = os.getenv('ZENDESK_SUBDOMAIN')
        if not self.api_token:
            print('ZENDESK_API_TOKEN environment variable is not set. Exiting.')
        self.auth = (f'{self.user_email}/token', self.api_token)
        self.headers = {'Content-Type': 'application/json'}

    def create_ticket(self, subject, description):
        try:
            url = f'https://{self.subdomain}/api/v2/tickets.json'
            data = {
                "ticket": {
                    "subject": subject,
                    "description": description
                }
            }
            response = requests.post(url, json=data, auth=self.auth, headers=self.headers)
            if response.status_code != 201:
                print('Status:', response.status_code, 'Problem with the request. Exiting.')
            return response.json()['ticket']['id']
        except Exception as e:
            print('Error:', e)
            return 12

    def get_user(self, email):
        try:
            url = f'https://{self.subdomain}/api/v2/users/search.json?query={email}'
            response = requests.get(url, auth=self.auth)
            if response.status_code != 200:
                print('Status:', response.status_code, 'Problem with the user search request. Exiting.')
            users = response.json().get('users')
            return users[0] if users else None
        except Exception as e:
            print('Error:', e)
            return None

    def create_user(self, name, email):
        try:
            url = f'https://{self.subdomain}/api/v2/users.json'
            data = {
                "user": {
                    "name": name,
                    "email": email,
                    "role": "end-user"
                }
            }
            response = requests.post(url, json=data, auth=self.auth)
            if response.status_code != 201:
                print('Status:', response.status_code, 'Problem with the user creation request. Exiting.')
            return response.json()['user']
        except Exception as e:
            print('Error:', e)
            return None

    def add_agent_comment(self, ticket_id, comment, requester_id=None):
        try:
            url = f'https://{self.subdomain}/api/v2/tickets/{ticket_id}.json'
            data = {
                "ticket": {
                    "comment": {
                        "body": comment
                    },
                    "requester_id": requester_id
                }
            }
            response = requests.put(url, json=data, auth=self.auth, headers=self.headers)
            if response.status_code != 200:
                print('Status:', response.status_code, 'Problem with the request. Exiting.')
        except Exception as e:
            print('Error:', e)

    def add_requester_comment(self, ticket_id, comment, requester_id=None):
        try:
            url = f'https://{self.subdomain}/api/v2/tickets/{ticket_id}.json'
            data = {
                "ticket": {
                    "comment": {
                        "body": comment,
                        "author_id": requester_id
                    }
                }
            }
            response = requests.put(url, json=data, auth=self.auth, headers=self.headers)
            if response.status_code != 200:
                print('Status:', response.status_code, 'Problem with the request. Exiting.')
        except Exception as e:
            print('Error:', e)
    
    def get_tickets(self):
        try:
            url = f'https://{self.subdomain}/api/v2/tickets.json'
            response = requests.get(url, auth=self.auth)
            if response.status_code != 200:
                print('Status:', response.status_code, 'Problem with the request. Exiting.')
            return response.json()['tickets']
        except Exception as e:
            print('Error:', e)
            return None

# Example usage
if __name__ == "__main__":
    zendesk_service = ZendeskService()
    user = zendesk_service.get_user("test.user@gmail.com")
    if user:
        print("Found user:", user)
    else:
        user = zendesk_service.create_user("Test User", "test.user@gmail.com")
        print("Created user:", user)
    ticket_id = zendesk_service.create_ticket("Test Ticket", "This is a test ticket created via API")
    print("Created ticket:", ticket_id)
    zendesk_service.add_requester_comment(ticket_id, "This is a Customer comment added to the ticket", user['id'])
    zendesk_service.add_agent_comment(ticket_id, "This is a Agent comment added to the ticket", user['id'])
    print("Ticket comments added.")
    tickets = zendesk_service.get_tickets()
    for ticket in tickets:
        print(ticket['subject'])
