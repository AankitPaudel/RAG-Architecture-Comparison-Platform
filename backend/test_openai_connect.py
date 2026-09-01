from dotenv import load_dotenv
import os
import openai

def test_openai_connection():
    # Load environment variables
    load_dotenv()
    
    # Get API key
    api_key = os.getenv('OPENAI_API_KEY')
    
    try:
        # Initialize OpenAI client
        client = openai.OpenAI(api_key=api_key)
        
        # Make a simple test request
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": "Say hello!"}],
            max_tokens=50
        )
        
        print("\nOpenAI API Test Results:")
        print("------------------------")
        print("✓ Connection successful!")
        print("✓ Response received!")
        print("\nTest response:", response.choices[0].message.content)
        
    except Exception as e:
        print("\nError testing OpenAI API:", str(e))

if __name__ == "__main__":
    test_openai_connection()