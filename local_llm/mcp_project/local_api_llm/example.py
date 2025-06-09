import requests
import json

def query_ollama(prompt):
    url = "http://192.168.176.1:11434/api/chat"
    headers = {"Content-Type": "application/json"}
    data = {
        "model": "qwen3:8b",
        "messages": [{"role": "user", "content": prompt}],
        "stream": True
    }

    response = requests.post(url, headers=headers, json=data, stream=True)
    # print(f"{response=}")
    result = ""
    for line in response.iter_lines():
        # print(f"{line=}")
        if not line:
            continue
        try:
            json_data = json.loads(line.decode("utf-8"))
            # print(f"{json_data=}")
            result += json_data.get("message", "").get("content", "")
        except json.JSONDecodeError:
            continue

    return result

# Example usage
output = query_ollama("Write me a haiku about development and its hardships.")
print(output)
