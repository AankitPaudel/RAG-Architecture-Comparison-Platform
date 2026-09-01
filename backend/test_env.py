from dotenv import load_dotenv
import os

def test_env():
    # Load environment variables
    load_dotenv()
    
    # Try to get API key
    api_key = os.getenv('OPENAI_API_KEY')
    
    if api_key:
        print("API Key found!")
        print("First few characters of key:", api_key[:7] + "...")
    else:
        print("No API key found in .env file")

if __name__ == "__main__":
    test_env()