import os
import sys
import logging
from pathlib import Path

# Ensure project root is in sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.core.llm_offline.engine import get_gemma_engine

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger("model-downloader")

def download_models(sizes=None):
    if sizes is None:
        sizes = ["2b", "9b"]
    
    logger.info("Initializing model downloads...")
    for size in sizes:
        try:
            logger.info(f"Checking Gemma {size.upper()}...")
            # This triggers auto_download in GemmaEngine.__init__
            engine = get_gemma_engine(size)
            if engine.is_available():
                logger.info(f"Gemma {size.upper()} is ready at {engine._model_path}")
            else:
                logger.error(f"Gemma {size.upper()} download failed or was incomplete.")
        except Exception as e:
            logger.error(f"Error downloading Gemma {size.upper()}: {e}")

if __name__ == "__main__":
    requested_sizes = sys.argv[1:] if len(sys.argv) > 1 else ["2b", "9b"]
    download_models(requested_sizes)
