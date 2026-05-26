import hashlib
from sentence_transformers import SentenceTransformer
import torch
from app.core.config import settings
from app.core.logging import logger

class LegalBertEngine:
    _instance = None
    _model = None
    _cache = {}  # In-memory hash cache: md5(text) -> tensor

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(LegalBertEngine, cls).__new__(cls)
            if settings.LEGALBERT_ENABLED:
                logger.info(f"Loading LegalBERT model: {settings.LEGALBERT_MODEL_NAME}")
                try:
                    cls._model = SentenceTransformer(settings.LEGALBERT_MODEL_NAME)
                    logger.info("LegalBERT model loaded successfully.")
                except Exception as e:
                    logger.error(f"Failed to load LegalBERT model: {e}")
                    # Allow non-fatal failure if fallback is desired, but for now we expect it to work
                    raise e
            else:
                logger.info("LegalBERT is disabled in config.")
        return cls._instance

    def _get_hash(self, text: str) -> str:
        return hashlib.md5(text.encode('utf-8')).hexdigest()

    def encode(self, text: str | list[str], skip_cache: bool = False):
        """
        Encode text(s) into embeddings using LegalBERT.
        Supports single string or list of strings.
        Uses in-memory caching if enabled.
        """
        if not self._model:
            # If model failed to load or is disabled, return 0-vector or raise
            # For robustness, we'll raise to strictly enforce dependencies if enabled
            if settings.LEGALBERT_ENABLED:
                 raise ValueError("LegalBERT Model not initialized")
            return None

        if isinstance(text, str):
            if settings.EMBEDDING_CACHE_ENABLED and not skip_cache:
                txt_hash = self._get_hash(text)
                if txt_hash in self._cache:
                    return self._cache[txt_hash]
            
            embedding = self._model.encode(text, convert_to_tensor=True)
            
            if settings.EMBEDDING_CACHE_ENABLED and not skip_cache:
                self._cache[txt_hash] = embedding
            return embedding

        elif isinstance(text, list):
            # Batch processing
            # Check cache for each item if enabled
            if settings.EMBEDDING_CACHE_ENABLED and not skip_cache:
                indices_to_compute = []
                texts_to_compute = []
                results = [None] * len(text)
                
                for i, t in enumerate(text):
                    h = self._get_hash(t)
                    if h in self._cache:
                        results[i] = self._cache[h]
                    else:
                        indices_to_compute.append(i)
                        texts_to_compute.append(t)
                
                if texts_to_compute:
                    computed_embeddings = self._model.encode(texts_to_compute, convert_to_tensor=True)
                    for idx, emb, txt in zip(indices_to_compute, computed_embeddings, texts_to_compute):
                        results[idx] = emb
                        self._cache[self._get_hash(txt)] = emb
                
                # Stack results into a single tensor if needed, or return list of tensors
                # SentenceTransformer .encode returns a tensor for list input usually
                # Here we reconstruct the tensor stack
                return torch.stack(results) if results else torch.tensor([])

            else:
                return self._model.encode(text, convert_to_tensor=True)

    def encode_batch(self, texts: list[str]):
        """Alias for encode(list) for clarity."""
        return self.encode(texts)

legalbert_engine = LegalBertEngine()
