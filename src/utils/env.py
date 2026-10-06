import os, sys
from pathlib import Path

def _detect():
    if "KAGGLE_KERNEL_RUN_TYPE" in os.environ:
        return "kaggle"
    if "google.colab" in sys.modules:
        return "colab"
    return "local"

ENV = _detect()
WORK = {"kaggle": Path("/kaggle/working"), "colab": Path("/content"), "local": Path.cwd()}[ENV]
RAW = WORK / "data" / "raw"
PROCESSED = WORK / "data" / "processed"
RAW.mkdir(parents=True, exist_ok=True)
PROCESSED.mkdir(parents=True, exist_ok=True)

def get_secret(name):
    if ENV == "colab":
        from google.colab import userdata
        return userdata.get(name)
    if ENV == "kaggle":
        from kaggle_secrets import UserSecretsClient
        return UserSecretsClient().get_secret(name)
    return os.environ[name]