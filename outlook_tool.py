import os
from O365 import Account
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

class OutlookTool:
    """Tool for interacting with Microsoft Outlook via Graph API."""
    
    def __init__(self):
        self.client_id = os.getenv("AZURE_CLIENT_ID")
        self.client_secret = os.getenv("AZURE_CLIENT_SECRET")
        self.tenant_id = os.getenv("AZURE_TENANT_ID")
        self.email_id = os.getenv("OUTLOOK_EMAIL_ID")
        
        if not all([self.client_id, self.client_secret, self.tenant_id, self.email_id]):
            # Graceful warning for missing env vars
            print("Warning: Outlook environment variables not fully set. Tool may fail.")
        
        credentials = (self.client_id, self.client_secret)
        self.account = Account(credentials)
        
        # We assume authentication is handled via a token file or previous CLI interaction
        # In a production environment, this would be a server-side OAuth flow
        self.authenticated = self.account.is_authenticated

    def get_unread_emails(self, limit=5):
        """Fetches unread emails from the inbox."""
        if not self.authenticated:
            return []
        
        mailbox = self.account.mailbox(resource=self.email_id)
        inbox = mailbox.inbox_folder()
        query = inbox.new_query().equals('isRead', False)
        messages = inbox.get_messages(limit=limit, query=query)
        return list(messages) if messages else []

    def send_reply(self, message_id, reply_body):
        """
        Sends an HTML-formatted reply to a specific email message.

        Args:
            message_id (str): The unique ID of the message to reply to (provided in the user prompt).
            reply_body (str): The HTML content of the reply message.
        """
        if not self.authenticated:
            print("Cannot send reply: Not authenticated.")
            return False
        
        mailbox = self.account.mailbox(resource=self.email_id)
        message = mailbox.get_message(message_id)
        
        if not message:
            print(f"Message {message_id} not found.")
            return False
            
        # create a reply draft
        reply = message.reply()
        reply.body = reply_body
        reply.body_type = 'HTML'
        reply.send()
        
        # Mark original as read
        message.mark_as_read()
        return True

    def send_new_email(self, to_address, subject, body):
        """Sends a brand new email."""
        if not self.authenticated:
            print("Cannot send email: Not authenticated.")
            return False
            
        message = self.account.new_message()
        message.to.add(to_address)
        message.subject = subject
        message.body = body
        message.body_type = 'HTML'
        message.send()
        return True
