import os
import re
from datetime import datetime
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()

class RAGSystem:
    def __init__(self, collection_name="knowledge_base"):
        # We'll stick to the same reliable local memory logic as the original
        self.documents = []

    def reset_collection(self):
        """Clears all documents from the memory."""
        self.documents = []
        print("Knowledge base cleared for sync.")

    def add_documents(self, documents, ids=None):
        """Adds documents to the local memory."""
        self.documents.extend(documents)

    def query(self, text, n_results=1):
        """Queries the local memory using a simple keyword search."""
        text = text.lower()
        
        # Simple keyword overlap scoring
        best_doc = None
        best_score = -1
        
        for doc in self.documents:
            score = sum(1 for word in text.split() if word in doc.lower())
            if score > best_score:
                best_score = score
                best_doc = doc
                
        if best_score > 0:
            return best_doc
        return None

class GeminiAgent:
    def __init__(self):
        # NEW: Using the unified Gen AI Client
        self.client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))
        self.model_id = 'gemini-2.0-flash' # Using the current stable flash model

    def process_and_reply(self, subject, body, knowledge_text, sender_name="Valued Customer"):
        """Processes the email and generates a response as the 'API Registrar' (HTML formatted)."""
        
        # --- FAST FALLBACK (Matching existing logic) ---
        code_match = re.search(r'(E\d{3})', f"{subject} {body}", re.IGNORECASE)
        if code_match:
            code = code_match.group(1).upper()
            found_line = None
            for line in knowledge_text.split('\n'):
                if re.search(fr'{code}\s*[-:=]', line, re.IGNORECASE):
                    found_line = line
                    break
            
            if found_line:
                consumer = found_line.strip().split()[-1]
                print(f"[{datetime.now().strftime('%H:%M:%S')}] Fast Matcher triggered for {code}: Found {consumer}!")
                return f"Dear {sender_name},<br><br>" \
                       f"The consumer of the given API {code} is found to be {consumer}.<br><br>" \
                       f"Please let us know if you require any further information regarding this mapping. " \
                       f"We are here to assist with your API registration needs.<br><br>" \
                       f"Thanks,<br>" \
                       f"API Registrar"

        # --- AI GENERATION WITH GOOGLE ADK (google-genai) ---
        system_instruction = f"""
        You are the "API Registrar". Help users find the consumer of a particular API (Ennn where nn = 001 to 999).
        
        KNOWLEDGE BASE:
        {knowledge_text}
        
        STRICT HTML FORMATTING RULES:
        1. Return your entire response in HTML format.
        2. Start with "Dear {sender_name},<br><br>".
        3. Mapping result: "The consumer of the given API Ennn (real API given in the mail) is found to be <extracted consumer>.<br><br>".
        4. Closing: "Please let us know if you require any further information regarding this mapping. We are here to assist with your API registration needs.<br><br>".
        5. Signature:
           Thanks,<br>
           API Registrar
        
        VERY IMPORTANT:
        - Use ONLY <br> for line breaks. Do not use plain text newlines.
        - Ensure "API Registrar" is on the line immediately following "Thanks," (single <br>).
        - Ensure a blank line (double <br>) before "Thanks,".
        - Extract ONLY the last word of the mapping line for the consumer.
        """

        prompt = f"Original Email (Subject: {subject}): {body}\n\nResponse:"
        
        # Using the new generate_content entry point
        response = self.client.models.generate_content(
            model=self.model_id,
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=system_instruction
            )
        )
        
        return response.text.strip()
