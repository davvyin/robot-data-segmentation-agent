import os


class DevConfig:
    UPLOAD_FOLDER = os.getenv("UPLOAD_FOLDER", "uploads")
    OPENAI_KEY = os.getenv("OPENAI_KEY")

config = {"dev": DevConfig}
