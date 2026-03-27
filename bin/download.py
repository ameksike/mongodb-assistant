"""Download GGUF models from Hugging Face to the models/ directory.

Usage:
    python bin/download.py                           # download default catalog model
    python bin/download.py --model phi-2             # catalog model (skips if file exists)
    python bin/download.py --list                    # list catalog + on-disk
    python bin/download.py --repo USER/REPO --file model.gguf
    python bin/download.py --force --model phi-2     # re-download even if present
    python bin/download.py --remove phi-2            # remove catalog model file
    python bin/download.py --remove-file custom.gguf # remove file by basename
    python bin/download.py --clean                   # remove all .gguf / .bin in models/
"""

import argparse
import json
import logging
import sys
from pathlib import Path
from urllib.request import urlretrieve
from urllib.error import URLError

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
MODELS_DIR = PROJECT_ROOT / "models"
CATALOG_PATH = PROJECT_ROOT / "cfg" / "models.json"
HF_BASE_URL = "https://huggingface.co"
MODEL_EXTENSIONS = {".gguf", ".bin"}


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
        return {
            p.name
            for p in self.modelsDir.iterdir()
            if p.is_file() and p.suffix.lower() in MODEL_EXTENSIONS
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

    def download(self, repo: str, filename: str, force: bool = False):
        """Download a model file from Hugging Face. Skips network if file exists unless force."""
        self.modelsDir.mkdir(parents=True, exist_ok=True)
        destPath = self.modelsDir / filename

        if destPath.exists() and not force:
            size = destPath.stat().st_size / (1024 * 1024)
            logger.info(f"Model already present, skipping download: {destPath} ({size:.0f} MB)")
            self._updateEnv(filename)
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

    def removeCatalogModel(self, modelName: str):
        """Remove on-disk file for a catalog entry."""
        _, filename = self.getModelInfo(modelName)
        self._removeFileIfExists(filename, label=f"catalog '{modelName}'")

    def removeFile(self, filename: str):
        """Remove models/<filename> if it exists."""
        base = Path(filename).name
        if base != filename:
            logger.warning("Using basename only: %s", base)
        self._removeFileIfExists(base, label=f"file '{base}'")

    def _removeFileIfExists(self, filename: str, label: str):
        path = self.modelsDir / filename
        if not self.modelsDir.exists():
            logger.info("models/ does not exist, nothing to remove for %s", label)
            return
        if not path.is_file():
            logger.info("Not found (skipped): %s", path)
            return
        path.unlink()
        logger.info("Removed %s -> %s", label, path)

    def cleanModelsDir(self):
        """Delete all .gguf and .bin files under models/."""
        if not self.modelsDir.exists():
            logger.info("models/ does not exist, nothing to clean.")
            return
        removed = 0
        for p in list(self.modelsDir.iterdir()):
            if p.is_file() and p.suffix.lower() in MODEL_EXTENSIONS:
                p.unlink()
                removed += 1
                logger.info("Removed: %s", p.name)
        if removed == 0:
            logger.info("No .gguf / .bin files found in models/.")
        else:
            logger.info("Cleaned %s model file(s) from models/.", removed)

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
    parser.add_argument("--model", type=str, metavar="NAME", help="Model key from cfg/models.json")
    parser.add_argument("--list", action="store_true", help="List catalog + on-disk models")
    parser.add_argument("--repo", type=str, help="Hugging Face repo (e.g. TheBloke/Mistral-7B-Instruct-v0.2-GGUF)")
    parser.add_argument("--file", type=str, help="Model filename (e.g. mistral-7b-instruct-v0.2.Q4_K_M.gguf)")
    parser.add_argument("--force", action="store_true", help="Re-download even if file already exists")
    parser.add_argument("--remove", type=str, metavar="NAME", help="Remove catalog model file from models/")
    parser.add_argument("--remove-file", type=str, dest="remove_file", metavar="FILE", help="Remove models/FILE by basename")
    parser.add_argument("--clean", action="store_true", help="Remove all .gguf and .bin files under models/")
    args = parser.parse_args()

    downloader = ModelDownloader()

    if args.list:
        downloader.listModels()
        return

    if args.clean:
        downloader.cleanModelsDir()
        return

    if args.remove:
        downloader.removeCatalogModel(args.remove)
        return

    if args.remove_file:
        downloader.removeFile(args.remove_file)
        return

    if args.repo and args.file:
        downloader.download(args.repo, args.file, force=args.force)
    elif args.model:
        repo, filename = downloader.getModelInfo(args.model)
        downloader.download(repo, filename, force=args.force)
    else:
        defaultModel = downloader.catalog.get("default")
        if defaultModel:
            logger.info(f"No model specified, using default: {defaultModel}")
            repo, filename = downloader.getModelInfo(defaultModel)
            downloader.download(repo, filename, force=args.force)
        else:
            parser.print_help()


if __name__ == "__main__":
    main()
