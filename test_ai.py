from services.ai_service import AIService
from dotenv import load_dotenv
import os

# Load env
load_dotenv()

def test_ai():
    print("Testing AI Service...")
    key = os.getenv("OPENROUTER_KEY")
    if not key:
        print("❌ Error: OPENROUTER_KEY is missing in .env")
        return

    print(f"Key found: {key[:5]}...")

    service = AIService()
    
    mock_prospect = {
        'name': 'Jean Dupont',
        'headline': 'CEO of TechCorp',
        'summary': 'Passionate about AI and automation.',
        'experience': 'Founder of DataSol, CTO at BigData Inc.'
    }
    
    print("Generating message for mock prospect...")
    response = service.generate_icebreaker(mock_prospect)
    
    print("\n--- AI Response ---")
    print(response)
    print("-------------------\n")
    
    if "Error" in response:
        print("❌ AI Generation Failed")
    else:
        print("✅ AI Generation Success")

if __name__ == "__main__":
    test_ai()
