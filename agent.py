import os
import time
import asyncio
from dotenv import load_dotenv
from google.adk import Agent, Runner
from google.adk.skills import load_skill_from_dir
from google.adk.sessions.in_memory_session_service import InMemorySessionService
from google.genai.types import Content, Part
from outlook_tool import OutlookTool
from rag_tool import RegistrarRAGTool

load_dotenv()

async def main():
    # Initialize Tool classes
    outlook = OutlookTool()
    rag_tool = RegistrarRAGTool()

    # Load the skill from the directory
    skill = load_skill_from_dir("./api-lookup-skill")

    # Initialize the Agent
    agent = Agent(
        name="api_registrar",
        instruction=skill.instructions,
        tools=[
            rag_tool.query_knowledge_base,
            outlook.send_reply
        ],
        model="gemini-flash-latest"
    )

    # Initialize Session Service and Runner
    session_service = InMemorySessionService()
    runner = Runner(
        app_name='api_registrar_app',
        agent=agent,
        session_service=session_service,
    )

    print("--- API Registrar AI Agent Started ---")
    print(f"Monitoring inbox: {os.getenv('OUTLOOK_EMAIL_ID')}")

    while True:
        try:
            # 1. Email Polling
            print("\nChecking for new inquiries...")
            emails = outlook.get_unread_emails(limit=5)

            for email in emails:
                print(f"Processing inquiry from: {email.sender.address}")
                
                # 2. Extract API code and check knowledge base (Hybrid Logic)
                import re
                api_code = None
                mapping_line = None
                
                # Extract API code (e.g., E001)
                match = re.search(r"[eE]\d{3}", f"{email.subject} {email.body}")
                if match:
                    api_code = match.group(0).upper()
                    if os.path.exists("knowledge.txt"):
                        with open("knowledge.txt", "r") as f:
                            for line in f:
                                if api_code in line.upper():
                                    mapping_line = line.strip()
                                    break
                
                # 3. Direct Reply based on Knowledge Base
                if mapping_line:
                    print(f"Direct Match Found for {api_code}: {mapping_line}")
                    html_reply = f"""
                    <html>
                    <body style="font-family: Arial, sans-serif;">
                        <p>Hello,</p>
                        <p>Thank you for your inquiry regarding the CBS API ecosystem.</p>
                        <p>Our records show the following consumer mapping for the requested API:</p>
                        <div style="background-color: #f4f4f4; padding: 15px; border-left: 5px solid #2c3e50; margin: 20px 0;">
                            <strong>API Code:</strong> {api_code}<br>
                            <strong>Consumer Mapping:</strong> {mapping_line.split('-')[-1].strip() if '-' in mapping_line else mapping_line}
                        </div>
                        <p>If you have further questions, please let us know.</p>
                        <hr>
                        <p style="font-size: 0.8em; color: #7f8c8d;">API Registrar Agent | Automated Response</p>
                    </body>
                    </html>
                    """
                else:
                    print(f"No direct mapping found for inquiry. Sending 'Not Found' template.")
                    html_reply = f"""
                    <html>
                    <body style="font-family: Arial, sans-serif;">
                        <p>Hello,</p>
                        <p>Thank you for your inquiry regarding the CBS API ecosystem.</p>
                        <p>Unfortunately, we could not find a consumer mapping for the API code <strong>'{api_code if api_code else "provided"}'</strong> in our current database.</p>
                        <p>Currently, we exclusively support mappings for APIs in the range <strong>E001 to E014</strong>.</p>
                        <p>Please contact the CBS API Administrator for further assistance.</p>
                        <hr>
                        <p style="font-size: 0.8em; color: #7f8c8d;">API Registrar Agent | Automated Response</p>
                    </body>
                    </html>
                    """
                
                success = outlook.send_reply(email.object_id, html_reply)
                if success:
                    print(f"Success: Reply sent to {email.sender.address} (Mode: Local Template)")
                else:
                    print(f"Failed to send reply to {email.sender.address}")
                
                continue # Move to next email
                
        except Exception as e:
            print(f"Error in polling loop: {str(e)}")
            await asyncio.sleep(60)

        await asyncio.sleep(30)

if __name__ == "__main__":
    asyncio.run(main())
