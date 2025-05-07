import os


class DevConfig:
    API_TOKEN = os.environ.get("API_TOKEN")
    UPLOAD_FOLDER = "uploads"
    OPENAI_KEY = "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"


config = {"dev": DevConfig}
