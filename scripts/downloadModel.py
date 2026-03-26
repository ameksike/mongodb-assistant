"""Download GGUF models from Hugging Face to the models/ directory.

Usage:
    python scripts/downloadModel.py                     # download default model
    python scripts/downloadModel.py --model mistral-7b-instruct
    python scripts/downloadModel.py --list              # list available models
    python scripts/downloadModel.py --repo USER/REPO --file model.gguf  # custom model
"""

import argparse
import json
import logging
import os
import sys
from pathlib import Path
from urllib.request import urlretrieve, Request, urlopen
from urllib.error import URLError

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
MODELS_DIR = PROJECT_ROOT / "models"
CATALOG_PATH = PROJECT_ROOT / "cfg" / "models.json"
HF_BASE_URL = "https://huggingface.co"


class ModelDownloader:
    """Downloads GGUF models from Hugging Face."""

    def __init__(self):
        self.modelsDir = MODELS_DIR
        self.catalog = self._loadCatalog()

    def _loadCatalog(self) -> dict:
        if CATALOG_PATH.exists():
            with open(CATALOG_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        return {"models": {}, "default": None}

    def _downloadedModelFilenames(self) -> set[str]:
        """Basenames of model files present under models/ (.gguf / .bin)."""
        if not self.modelsDir.exists():
            return set()
        exts = {".gguf", ".bin"}
        return {
            p.name
            for p in self.modelsDir.iterdir()
            if p.is_file() and p.suffix.lower() in exts
        }

    def _formatFileSizeMb(self, path: Path) -> str:
        mb = path.stat().st_size / (1024 * 1024)
        return f"{mb:.0f} MB"

    def listModels(self):
        """Print catalog models and files already present in models/."""
        onDisk = self._downloadedModelFilenames()
        defaultName = self.catalog.get("default", "")

        print("\nCatalog (available to download):\n")
        if not self.catalog.get("models"):
            print("  (no entries in cfg/models.json)\n")
        else:
            for name, info in self.catalog["models"].items():
                marker = " (default)" if name == defaultName else ""
                fname = info["file"]
                status = "downloaded" if fname in onDisk else "not on disk"
                print(f"  {name}{marker}  [{status}]")
                print(f"    {info['description']}")
                print(f"    repo: {info['repo']}")
                print(f"    file: {fname}")
                if fname in onDisk:
                    path = self.modelsDir / fname
                    print(f"    local: models/{fname} ({self._formatFileSizeMb(path)})")
                print()

        print("On disk (models/):\n")
        if not onDisk:
            print("  (no .gguf or .bin files in models/)\n")
        else:
            catalogByFile = {info["file"]: n for n, info in self.catalog.get("models", {}).items()}
            for fname in sorted(onDisk):
                path = self.modelsDir / fname
                catNote = f"  (catalog: {catalogByFile[fname]})" if fname in catalogByFile else "  (custom / not in catalog)"
                print(f"  {fname}  ({self._formatFileSizeMb(path)}){catNote}")
            print()

    def getModelInfo(self, modelName: str) -> tuple:
        """Return (repo, filename) for a catalog model name."""
        if modelName not in self.catalog["models"]:
            available = ", ".join(self.catalog["models"].keys())
            logger.error(f"Model '{modelName}' not found. Available: {available}")
            sys.exit(1)
        info = self.catalog["models"][modelName]
        return info["repo"], info["file"]

    def buildUrl(self, repo: str, filename: str) -> str:
        return f"{HF_BASE_URL}/{repo}/resolve/main/{filename}"

    def download(self, repo: str, filename: str):
        """Download a model file from Hugging Face."""
        self.modelsDir.mkdir(parents=True, exist_ok=True)
        destPath = self.modelsDir / filename

        if destPath.exists():
            size = destPath.stat().st_size / (1024 * 1024)
            logger.info(f"Model already exists: {destPath} ({size:.0f} MB)")
            response = input("Re-download? [y/N]: ").strip().lower()
            if response != "y":
                logger.info("Skipped.")
                return

        url = self.buildUrl(repo, filename)
        logger.info(f"Downloading: {filename}")
        logger.info(f"From: {url}")
        logger.info(f"To: {destPath}")
        print()

        try:
            urlretrieve(url, str(destPath), reporthook=self._progressHook)
            print()
            size = destPath.stat().st_size / (1024 * 1024)
            logger.info(f"Download complete: {size:.0f} MB")
            self._updateEnv(filename)
        except URLError as e:
            logger.error(f"Download failed: {e}")
            if destPath.exists():
                destPath.unlink()
            sys.exit(1)
        except KeyboardInterrupt:
            print()
            logger.info("Download cancelled.")
            if destPath.exists():
                destPath.unlink()
            sys.exit(1)

    def _progressHook(self, blockNum: int, blockSize: int, totalSize: int):
        downloaded = blockNum * blockSize
        if totalSize > 0:
            percent = min(100, downloaded * 100 / totalSize)
            downloadedMb = downloaded / (1024 * 1024)
            totalMb = totalSize / (1024 * 1024)
            bar = "=" * int(percent // 2) + ">" + " " * (50 - int(percent // 2))
            sys.stdout.write(f"\r  [{bar}] {percent:5.1f}% ({downloadedMb:.0f}/{totalMb:.0f} MB)")
            sys.stdout.flush()

    def _updateEnv(self, filename: str):
        """Update LOCAL_MODEL_PATH in cfg/.env if it exists."""
        envPath = PROJECT_ROOT / "cfg" / ".env"
        if not envPath.exists():
            return
        newPath = f"models/{filename}"
        lines = envPath.read_text(encoding="utf-8").splitlines()
        updated = False
        for i, line in enumerate(lines):
            if line.startswith("LOCAL_MODEL_PATH="):
                lines[i] = f"LOCAL_MODEL_PATH={newPath}"
                updated = True
                break
        if updated:
            envPath.write_text("\n".join(lines) + "\n", encoding="utf-8")
            logger.info(f"Updated cfg/.env: LOCAL_MODEL_PATH={newPath}")


def main():
    parser = argparse.ArgumentParser(description="Download GGUF models from Hugging Face")
    parser.add_argument("--model", type=str, help="Model name from cfg/models.json catalog")
    parser.add_argument("--list", action="store_true", help="List available models")
    parser.add_argument("--repo", type=str, help="Hugging Face repo (e.g. TheBloke/Mistral-7B-Instruct-v0.2-GGUF)")
    parser.add_argument("--file", type=str, help="Model filename (e.g. mistral-7b-instruct-v0.2.Q4_K_M.gguf)")
    args = parser.parse_args()

    downloader = ModelDownloader()

    if args.list:
        downloader.listModels()
        return

    if args.repo and args.file:
        downloader.download(args.repo, args.file)
    elif args.model:
        repo, filename = downloader.getModelInfo(args.model)
        downloader.download(repo, filename)
    else:
        defaultModel = downloader.catalog.get("default")
        if defaultModel:
            logger.info(f"No model specified, using default: {defaultModel}")
            repo, filename = downloader.getModelInfo(defaultModel)
            downloader.download(repo, filename)
        else:
            parser.print_help()


if __name__ == "__main__":
    main()
