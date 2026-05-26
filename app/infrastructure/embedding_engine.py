from sentence_transformers import SentenceTransformer
from app.core.config import settings
from app.core.logging import logger

class EmbeddingEngine:
    _instance = None
    _model = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(EmbeddingEngine, cls).__new__(cls)
            logger.info(f"Loading embedding model: {settings.EMBEDDING_MODEL_NAME}")
            try:
                cls._model = SentenceTransformer(settings.EMBEDDING_MODEL_NAME)
                logger.info("Embedding model loaded successfully.")
            except Exception as e:
                logger.error(f"Failed to load embedding model: {e}")
                raise e
        return cls._instance

    def encode(self, text: str | list[str]):
        if not self._model:
             raise ValueError("Model not initialized")
        return self._model.encode(text, convert_to_tensor=True)

embedding_engine = EmbeddingEngine()
