import os
from agent_logic import GeminiAgent
from dotenv import load_dotenv

load_dotenv()

def test_adk():
    print("Testing Google ADK (google-genai) implementation...")
    agent = GeminiAgent()
    
    knowledge = """
    E001 - Consumer: Payments
    E002 - Consumer: Checkout
    E003 - Consumer: Inventory
    """
    
    # Test 1: Fast Matcher
    print("\n--- Test 1: Fast Matcher ---")
    resp1 = agent.process_and_reply("Mapping for E002", "Please provide mapping", knowledge, "Shadab")
    print(f"Response:\n{resp1}")
    assert "Checkout" in resp1
    assert "Shadab" in resp1
    
    # Test 2: AI Generation
    print("\n--- Test 2: AI Generation ---")
    resp2 = agent.process_and_reply("Who uses E003?", "I need to know the consumer for E003.", knowledge, "Shadab")
    print(f"Response:\n{resp2}")
    assert "Inventory" in resp2
    assert "<br>" in resp2
    
    print("\nVerification successful!")

if __name__ == "__main__":
    test_adk()
