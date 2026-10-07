import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data"
RAW = DATA / "raw"
PROCESSED = DATA / "processed"
TREINO = DATA / "treino"
FIGURES = ROOT / "reports" / "figures"

for p in (RAW, PROCESSED, TREINO, FIGURES):
    p.mkdir(parents=True, exist_ok=True)

if "KAGGLE_KERNEL_RUN_TYPE" in os.environ:
    ENV = "kaggle"
elif "google.colab" in sys.modules:
    ENV = "colab"
else:
    ENV = "local"


def get_secret(name):
    if ENV == "colab":
        from google.colab import userdata
        return userdata.get(name)
    if ENV == "kaggle":
        from kaggle_secrets import UserSecretsClient
        return UserSecretsClient().get_secret(name)
    return os.environ[name]