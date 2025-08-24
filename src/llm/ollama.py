import requests
import json
from settings import config

OLLAMA_URL = config["OLLAMA_URL"]
OLLAMA_KEEP_ALIVE = config["OLLAMA_KEEP_ALIVE"]

class OllamaClient:
    def __init__(self, url=OLLAMA_URL):
        self.url = url

    def _request(self, method, endpoint, **kwargs):
        url = f"{self.url}/{endpoint}"
        try:
            response = requests.request(method, url, **kwargs)
            response.raise_for_status()
            if kwargs.get('stream', False):
                return response.iter_lines()
            return response.json()
        except requests.ConnectionError as e:
            print(f"[ERROR] Ollama Not Running, please start the server and try again.")
            exit(1)
        except Exception as e:
            raise Exception(f"Error occurred: {e}")

    def list_models(self):
        """List all available models."""
        response = self._request("GET", "api/tags")
        return response["models"]

    def pull_model(self, name, stream=False):
        """Pull a model by name."""
        payload = {"name": name, "stream": stream}
        return self._request("POST", "api/pull", json=payload)

    def chat(self, messages, model="qwen3:0.6b", stream=False, **kwargs):
        """Send a chat message."""
        payload = {
            "messages": messages,
            "model": model,
            "keep_alive": OLLAMA_KEEP_ALIVE,
            "stream": stream
        }
        payload.update(kwargs)
        response = self._request("POST", "api/chat", json=payload, stream=stream)
        return response

if __name__ == "__main__":
    client = OllamaClient()

    ##########################
    ##########################

    models = client.list_models()
    print("Available models:")
    for model in models:
        print(f" - {model['name']}")
        print(f"   Parameters: {model['details']['parameter_size']}")
        print(f"   Size: {model['size'] / (1024 * 1024):.1f} MB")

    ##########################
    ##########################

    # response = client.chat(messages=[
    #     {"role": "system", "content": "You are a helpful assistant."},
    #     {"role": "user", "content": "Why is the sky blue?"}
    # ], stream=False)

    # print("🤖 Model Response:")
    # print(response["message"].get("content", ""))

    # print("\n====================================")
    # print("Total Duration:", response["total_duration"])
    # print("Load Duration:", response["load_duration"])
    # print("Prompt Eval Count:", response["prompt_eval_count"])
    # print("Prompt Eval Duration:", response["prompt_eval_duration"])
    # print("Eval Count:", response["eval_count"])
    # print("Eval Duration:", response["eval_duration"])
    # print("====================================")


    ##########################
    ##########################

    # response_stream = client.chat(messages=[
    #     {"role": "system", "content": "You are a helpful assistant."},
    #     {"role": "user", "content": "Why is the sky blue?"}
    # ], stream=True)
    # for line in response_stream:
    #     if line:
    #         try:
    #             message = json.loads(line.decode('utf-8'))
    #             print(message["message"].get('content', ''), end="")
    #             if message.get("done", False):
    #                 print("\n====================================")
    #                 print("Total Duration:", message["total_duration"])
    #                 print("Load Duration:", message["load_duration"])
    #                 print("Prompt Eval Count:", message["prompt_eval_count"])
    #                 print("Prompt Eval Duration:", message["prompt_eval_duration"])
    #                 print("Eval Count:", message["eval_count"])
    #                 print("Eval Duration:", message["eval_duration"])
    #                 print("====================================")
    #         except json.JSONDecodeError:
    #             print("Error decoding JSON from stream.")
