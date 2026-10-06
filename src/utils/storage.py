import urllib.request
 
from src.utils.env import PROCESSED
from src import config as C
 
 
def get_parquet(force=False):
folder = PROCESSED / C.DATA_VERSION
folder.mkdir(parents=True, exist_ok=True)
path = folder / C.PARQUET_NAME
if force or not path.exists():
url = (
f"https://github.com/{C.GITHUB_REPO}/releases/download/"
f"{C.DATA_VERSION}/{C.PARQUET_NAME}"
)
print(f"Baixando {url} ...")
urllib.request.urlretrieve(url, path)
return path
