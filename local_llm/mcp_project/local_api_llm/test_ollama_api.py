import requests
import json

def test_ollama_api():
    """Test Ollama API connection and function calling"""
    
    ollama_url = "http://192.168.176.1:11434"
    
    print("🧪 Testing Ollama API Connection from WSL...")
    
    # Test 1: Check if Ollama is accessible
    try:
        response = requests.get(f"{ollama_url}/api/tags", timeout=5)
        if response.status_code == 200:
            models = response.json()
            model_names = [model['name'] for model in models['models']]
            print(f"✅ Connected to Ollama successfully!")
            print(f"Available models: {model_names}")
        else:
            print(f"❌ HTTP Error: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print(f"❌ Cannot connect to Ollama at {ollama_url}")
        print("Troubleshooting:")
        print("1. Make sure Ollama is running on Windows")
        print("2. Check Windows Firewall settings")
        print("3. Try: curl http://192.168.176.1:11434/api/tags")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    
    # Test 2: Simple chat request
    print(f"\n🔄 Testing basic chat...")
    try:
        chat_data = {
            "model": "qwen3:8b",  # Change to your model
            "messages": [{"role": "user", "content": "Hello! Just say 'Hi' back."}],
            "stream": False
        }
        
        response = requests.post(f"{ollama_url}/api/chat", json=chat_data, timeout=30)
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Basic chat works!")
            print(f"Response: {result['message']['content']}")
        else:
            print(f"❌ Chat request failed: {response.status_code}")
            print(f"Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Chat test failed: {e}")
        return False
    
    # Test 3: Function calling
    print(f"\n🔧 Testing function calling...")
    try:
        tools = [
            {
                "type": "function",
                "function": {
                    "name": "get_weather",
                    "description": "Get current weather",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "location": {"type": "string", "description": "City name"}
                        },
                        "required": ["location"]
                    }
                }
            }
        ]
        
        function_data = {
            "model": "qwen3:8b",  # Change to your model
            "messages": [{"role": "user", "content": "What's the weather in Paris?"}],
            "tools": tools,
            "stream": False
        }
        
        response = requests.post(f"{ollama_url}/api/chat", json=function_data, timeout=30)
        if response.status_code == 200:
            result = response.json()
            message = result['message']
            
            if 'tool_calls' in message:
                print(f"✅ Function calling works!")
                print(f"Model wants to call: {message['tool_calls'][0]['function']['name']}")
                print(f"With arguments: {message['tool_calls'][0]['function']['arguments']}")
            else:
                print(f"⚠️  Model responded but didn't use function calling")
                print(f"Response: {message['content']}")
        else:
            print(f"❌ Function calling test failed: {response.status_code}")
            print(f"Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Function calling test failed: {e}")
        return False
    
    print(f"\n🎉 All tests passed! Your setup should work with the MCP chatbot.")
    return True

if __name__ == "__main__":
    test_ollama_api()