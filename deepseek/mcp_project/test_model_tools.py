import ollama
import json

def test_model_tools(model_name):
    """Test if a model supports function calling"""
    
    # Simple test tool
    test_tools = [
        {
            "type": "function",
            "function": {
                "name": "get_current_time",
                "description": "Get the current time",
                "parameters": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            }
        }
    ]
    
    test_messages = [
        {"role": "user", "content": "What time is it?"}
    ]
    
    try:
        response = ollama.chat(
            model=model_name,
            messages=test_messages,
            tools=test_tools
        )
        print(f"✅ {model_name}: Supports function calling")
        return True
    except Exception as e:
        if "does not support tools" in str(e):
            print(f"❌ {model_name}: Does not support function calling")
        else:
            print(f"❓ {model_name}: Error testing - {e}")
        return False

def main():
    print("🧪 Testing models for function calling support...\n")
    
    # Get available models
    try:
        models = ollama.list()
        available_models_names = [model['model'] for model in models['models']]
        
        print("Available models:")
        for model_name in available_models_names:
            print(f"  • {model_name}")
        print()
        
    except Exception as e:
        print(f"Error listing models: {e}")
        return
    
    # Models known to support function calling
    recommended_models = [
        "llama3.2:3b",
        "llama3.2:1b", 
        "llama3.1:8b",
        "qwen2.5:3b",
        "qwen2.5:1.5b",
        "mistral:7b",
        "gemma2:9b",
        "gemma2:2b"
    ]
    
    print("Testing recommended models for function calling:")
    print("=" * 50)
    
    working_models = []
    
    for model in recommended_models:
        if model in available_models_names:
            if test_model_tools(model):
                working_models.append(model)
        else:
            print(f"⏳ {model}: Not installed (run 'ollama pull {model}' to install)")
    
    print("\n" + "=" * 50)
    print("SUMMARY:")
    if working_models:
        print("✅ Models that support function calling:")
        for model in working_models:
            print(f"  • {model}")
        print(f"\nRecommended: {working_models[0]} (good balance of size and capability)")
    else:
        print("❌ No models with function calling support found.")
        print("Try installing one of these:")
        print("  ollama pull llama3.2:3b")
        print("  ollama pull qwen2.5:3b")
        print("  ollama pull mistral:7b")

if __name__ == "__main__":
    main()