import os
from O365 import Account
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

class OutlookAgent:
    def __init__(self):
        # O365 uses Client ID and Client Secret
        self.client_id = os.getenv("AZURE_CLIENT_ID")
        self.client_secret = os.getenv("AZURE_CLIENT_SECRET")
        self.tenant_id = os.getenv("AZURE_TENANT_ID")
        self.email_id = os.getenv("OUTLOOK_EMAIL_ID")
        
        if not all([self.client_id, self.client_secret, self.tenant_id, self.email_id]):
            raise ValueError("All Azure environment variables and OUTLOOK_EMAIL_ID must be set.")
        
        # Authenticate using Authorization Code flow (standard for personal accounts)
        credentials = (self.client_id, self.client_secret)
        self.account = Account(credentials) # Default is authorization flow
        
        if not self.account.is_authenticated:
            # This will trigger an interactive login in the terminal
            # The user will need to visit a URL and paste back the redirect URL
            print("\n--- ACTION REQUIRED ---")
            print("Since you are using a PERSONAL account, you must authorize the app manually once.")
            self.account.authenticate(scopes=['User.Read', 'Mail.ReadWrite', 'Mail.Send'], redirect_uri='http://localhost:8080')
            print("Authentication successful! Token saved to o365_token.txt")
        else:
            print("Authenticated using saved token.")
        
        # Get the mailbox for the specified user
        self.mailbox = self.account.mailbox(resource=self.email_id)

    async def get_unread_emails(self):
        """Fetches unread emails from the specified inbox."""
        # Note: O365 is synchronous by design, but we can treat it as async or use it directly
        # For simplicity in this script, we'll just call it synchronously
        inbox = self.mailbox.inbox_folder()
        # Query for unread messages
        query = inbox.new_query().equals('isRead', False)
        messages = inbox.get_messages(limit=3, query=query)
        return list(messages) if messages else []

    async def reply_to_email(self, message, comment):
        """Sends a response as a new message to keep the subject line identical."""
        try:
            # Extract the sender's address
            sender_address = message.sender.address if message.sender else None
            if not sender_address:
                print(f"[{datetime.now().strftime('%H:%M:%S')}] Cannot reply: No sender address.")
                return

            # Create a new message manually to guarantee identical subject line
            new_message = self.account.new_message()
            new_message.to.add(sender_address)
            new_message.subject = message.subject # Strict: Use the exact same subject line
            # Set body and ensure it is treated as HTML for correct formatting
            new_message.body = comment
            new_message.body_type = 'HTML'
            
            new_message.send()
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Reply sent to {sender_address} with identical subject.")
        except Exception as e:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] ERROR in reply_to_email: {str(e)}")
            raise e

    async def mark_as_read(self, message):
        """Marks an email as read."""
        message.mark_as_read()
        print(f"Message {message.object_id} marked as read")
