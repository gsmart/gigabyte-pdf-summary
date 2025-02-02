import requests
import sys

OLLAMA_URL = "http://127.0.0.1:11434/api/generate"  # Ollama API URL

def query_ollama(prompt, model="deepseek-r1:1.5b"):
    """ Sends a request to Ollama's API and returns the response """
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False  # Set to True if you want incremental responses
    }
    try:
        response = requests.post(OLLAMA_URL, json=payload)
        response.raise_for_status()
        return response.json().get("response", "⚠️ No response received.")
    except requests.exceptions.RequestException as e:
        return f"🚨 Ollama API error: {e}"

def main():
    print("🟢 Connected to Ollama API")
    print("🟡 Type your input below. Type 'exit' to quit.\n")

    while True:
        user_input = input("> ")
        if user_input.lower() == "exit":
            print("👋 Exiting...")
            break

        print("🟢 Sending request to Ollama API...")
        response = query_ollama(user_input)
        print(f"📝 Ollama Response: {response}")

if __name__ == "__main__":
    main()
