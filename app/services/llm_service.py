from google import genai
from app.core.config import settings
from app.core.logging import logger

class LLMService:
    def __init__(self):
        self.gemini_key = settings.GEMINI_API_KEY
        self.client = None
        
        if self.gemini_key:
            try:
                self.client = genai.Client(api_key=self.gemini_key)
                self.provider = "gemini"
            except Exception as e:
                logger.error(f"Failed to initialize Gemini client: {e}")
                self.provider = "mock"
        else:
             logger.warning("No Gemini API key found. LLM features will be disabled.")
             self.provider = "mock"

    async def generate_explanation(self, clause_text: str, clause_type: str, risk_score: float, reasons: list[str]) -> str:
        prompt = f"""
        Clause Type: {clause_type}
        Risk Score: {risk_score}
        Risk Reasons: {', '.join(reasons)}
        Clause Text: "{clause_text}"

        Explain clearly why this clause is risky using simple business English. Be concise.
        """
        return await self._call_llm(prompt)

    async def generate_rewrite(self, clause_text: str) -> str:
        prompt = f"""
        Rewrite this clause using safer, balanced, industry-standard legal language.
        Include liability cap if missing. Keep it professional.
        
        Clause Text: "{clause_text}"
        """
        return await self._call_llm(prompt)

    async def _call_llm(self, prompt: str) -> str:
        if self.provider == "gemini" and self.client:
            try:
                response = self.client.models.generate_content(
                    model='gemini-2.5-flash', contents=prompt
                )
                return response.text
            except Exception as e:
                logger.error(f"Gemini Error: {e}")
                return "Error generating content."
        
        return "LLM Service not configured."

llm_service = LLMService()
