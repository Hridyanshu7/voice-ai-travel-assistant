import asyncio
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

async def test_all_apis():
    print("="*60)
    print("TESTING ALL AVAILABLE APIs")
    print("="*60)
    
    # Test 1: Gemini Direct
    print("\n1. Testing Gemini API (Direct)...")
    try:
        import google.generativeai as genai
        api_key = os.getenv("GEMINI_API_KEY")
        if api_key:
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel('gemini-2.0-flash-exp')
            response = model.generate_content("Say hello in 5 words")
            print(f"   ✅ SUCCESS: {response.text}")
        else:
            print("   ❌ No API key found")
    except Exception as e:
        print(f"   ❌ FAILED: {str(e)[:100]}")
    
    # Test 2: Claude
    print("\n2. Testing Claude API...")
    try:
        import httpx
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if api_key and api_key != "YOUR_ANTHROPIC_API_KEY_HERE":
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    "https://api.anthropic.com/v1/messages",
                    headers={
                        "x-api-key": api_key,
                        "anthropic-version": "2023-06-01",
                        "content-type": "application/json"
                    },
                    json={
                        "model": "claude-3-5-haiku-20241022",
                        "max_tokens": 50,
                        "messages": [{"role": "user", "content": "Say hello in 5 words"}]
                    }
                )
                if response.status_code == 200:
                    result = response.json()
                    print(f"   ✅ SUCCESS: {result['content'][0]['text']}")
                else:
                    print(f"   ❌ FAILED: Status {response.status_code}")
        else:
            print("   ⚠️  No API key configured")
    except Exception as e:
        print(f"   ❌ FAILED: {str(e)[:100]}")
    
    # Test 3: OpenRouter
    print("\n3. Testing OpenRouter API...")
    try:
        import httpx
        api_key = os.getenv("OPENROUTER_API_KEY")
        if api_key:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    "https://openrouter.ai/api/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": "meta-llama/llama-3.2-3b-instruct:free",
                        "messages": [{"role": "user", "content": "Say hello in 5 words"}]
                    }
                )
                if response.status_code == 200:
                    result = response.json()
                    print(f"   ✅ SUCCESS: {result['choices'][0]['message']['content']}")
                else:
                    print(f"   ❌ FAILED: Status {response.status_code} - Rate limited")
        else:
            print("   ❌ No API key found")
    except Exception as e:
        print(f"   ❌ FAILED: {str(e)[:100]}")
    
    print("\n" + "="*60)
    print("RECOMMENDATION:")
    print("="*60)
    print("Based on the results above:")
    print("- If Gemini works: You're good to go! (Free & reliable)")
    print("- If Claude works: Excellent quality responses")
    print("- If OpenRouter works: Good fallback option")
    print("- If none work: Check your API keys in .env file")

if __name__ == "__main__":
    asyncio.run(test_all_apis())
