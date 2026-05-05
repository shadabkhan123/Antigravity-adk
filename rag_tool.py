import os
from google.cloud import aiplatform
from vertexai.preview import rag
import vertexai
from dotenv import load_dotenv

load_dotenv()

class RegistrarRAGTool:
    """Tool for querying the Vertex AI RAG Engine corpus."""
    
    def __init__(self):
        self.project_id = os.getenv("GOOGLE_CLOUD_PROJECT")
        self.location = os.getenv("GOOGLE_CLOUD_REGION", "us-central1")
        self.corpus_id = os.getenv("VERTEX_AI_RAG_CORPUS_ID")
        
        if not self.project_id:
            print("Warning: GOOGLE_CLOUD_PROJECT not set.")
        
        # Initialize Vertex AI
        vertexai.init(project=self.project_id, location=self.location)

    def query_knowledge_base(self, query_text: str):
        """
        Queries the RAG corpus to find the consumer mapping.
        Falls back to a local knowledge.txt if RAG is unavailable.
        """
        rag_result = "No mapping found."
        
        # 1. Try RAG Engine if configured
        if self.corpus_id and self.project_id:
            try:
                response = rag.retrieval_query(
                    rag_resources=[rag.RagResource(rag_corpus=self.corpus_id)],
                    text=query_text,
                    similarity_top_k=1,
                )
                if response.contexts:
                    rag_result = response.contexts[0].text
                    return rag_result
            except Exception as e:
                print(f"RAG Engine error: {str(e)}")

        # 2. Fallback to local knowledge.txt
        print("Using local knowledge.txt fallback...")
        try:
            if os.path.exists("knowledge.txt"):
                with open("knowledge.txt", "r") as f:
                    content = f.read().lower()
                    # Simple keyword matching for the API code
                    import re
                    # Look for codes like E001
                    match = re.search(r"[e]\d{3}", query_text.lower())
                    if match:
                        api_code = match.group(0).upper()
                        print(f"Searching for API Code: {api_code}")
                        for line in content.split("\n"):
                            if api_code in line.upper():
                                return line.strip()
            
            return "No mapping found for this API in the registrar database."
            
        except Exception as e:
            return f"Error in mapping lookup: {str(e)}"

    def get_corpus_status(self):
        """Checks the status of the RAG corpus."""
        try:
            corpus = rag.get_rag_corpus(name=self.corpus_id)
            return f"Corpus {corpus.display_name} is active."
        except Exception as e:
            return f"Error: {str(e)}"
