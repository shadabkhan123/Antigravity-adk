import asyncio
import os
import time
from datetime import datetime
from microsoft_graph import OutlookAgent
# New: Importing from the ADK-based agent_logic
from agent_logic import RAGSystem, GeminiAgent
from dotenv import load_dotenv

load_dotenv()

async def main():
    print(f"[{datetime.now().strftime('%H:%M:%S')}] ADK VERSION: Initializing OutlookAgent...")
    outlook = OutlookAgent()
    print(f"[{datetime.now().strftime('%H:%M:%S')}] ADK VERSION: Initializing RAGSystem...")
    rag = RAGSystem()
    print(f"[{datetime.now().strftime('%H:%M:%S')}] ADK VERSION: Initializing GeminiAgent (Google ADK Library)...")
    gemini = GeminiAgent()

    # Seed the RAG with data from knowledge.txt
    if os.path.exists("knowledge.txt"):
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Loading knowledge.txt...")
        with open("knowledge.txt", "r") as f:
            content = f.read()
            # Split by lines and remove empty ones
            paragraphs = [p.strip() for p in content.split("\n") if p.strip()]
            if paragraphs:
                print(f"[{datetime.now().strftime('%H:%M:%S')}] Syncing {len(paragraphs)} items to local memory...")
                rag.reset_collection()
                rag.add_documents(paragraphs)
                print(f"[{datetime.now().strftime('%H:%M:%S')}] Knowledge sync complete.")
    else:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] No knowledge.txt found.")

    print(f"[{datetime.now().strftime('%H:%M:%S')}] ADK VERSION: Starting the polling loop...")

    while True:
        try:
            start_fetch = time.perf_counter()
            emails = await outlook.get_unread_emails()
            end_fetch = time.perf_counter()
            
            if not emails:
                # print(f"[{datetime.now().strftime('%H:%M:%S')}] No unread emails found (Fetch: {end_fetch - start_fetch:.2f}s). Waiting 30s...")
                pass
            
            for email in emails:
                subject = email.subject or "No Subject"
                body = email.body
                sender_name = email.sender.name if email.sender and email.sender.name else "Valued Customer"

                print(f"[{datetime.now().strftime('%H:%M:%S')}] Processing: [{subject}] (ADK Mode)")
                
                start_ai = time.perf_counter()
                knowledge_data = ""
                if os.path.exists("knowledge.txt"):
                    with open("knowledge.txt", "r") as f:
                        knowledge_data = f.read()
                
                response_text = gemini.process_and_reply(subject, body, knowledge_data, sender_name)
                end_ai = time.perf_counter()
                
                start_reply = time.perf_counter()
                await outlook.reply_to_email(email, response_text)
                end_reply = time.perf_counter()
                
                await outlook.mark_as_read(email)
                
                total_duration = end_ai - start_ai + end_reply - start_reply
                print(f"[{datetime.now().strftime('%H:%M:%S')}] SUCCESS: Message handled via Google ADK.")
                print(f"      - AI Duration:     {end_ai - start_ai:.2f}s")
                print(f"      - Reply Duration:  {end_reply - start_reply:.2f}s")
                print(f"      - Total Latency:   {total_duration:.2f}s")

        except Exception as e:
            if "quota" in str(e).lower() or "429" in str(e):
                print(f"[{datetime.now().strftime('%H:%M:%S')}] Quota reached. Waiting 60s...")
                await asyncio.sleep(60)
            else:
                print(f"[{datetime.now().strftime('%H:%M:%S')}] ERROR in ADK main loop: {str(e)}")

        await asyncio.sleep(30)

if __name__ == "__main__":
    asyncio.run(main())
