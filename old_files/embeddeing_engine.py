if embedding_model.find("ollama-") == 0:
            self.embeddings = OllamaEmbedder(
                url="http://localhost:11434",
                model_name=embedding_model.replace("ollama-", ""),
                timeout=ollama_timeout
            )
        else:
            raise ValueError("Supported models: ollama-<ollama models>")