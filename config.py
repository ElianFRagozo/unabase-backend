import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    PORT: int = int(os.getenv("PORT", 8000))
    HOST: str = os.getenv("HOST", "0.0.0.0")
    DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"
    
    # Validación de configuración
    def validate(self):
        if not self.OPENAI_API_KEY or self.OPENAI_API_KEY == "":
            print("⚠️  WARNING: OPENAI_API_KEY not configured. Some features may not work.")
            # No lanzar error para permitir que el servidor se ejecute

settings = Settings()
