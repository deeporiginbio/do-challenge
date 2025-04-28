from dotenv import load_dotenv

load_dotenv()

from typing import (
    Any,
    Dict,
    List,
    Optional,
    Union,
)

from pydantic import (
    AnyHttpUrl,
    MongoDsn,
    validator
)
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    SECRET_KEY: str = 'MHnx4BGNFI_SAyH7aF1KBlP0Sx1bk47LvIRApjvtI4Y'
    BACKEND_CORS_ORIGINS: List[AnyHttpUrl] = []
    FRONTEND_URL: str = "http://localhost:3000"

    APPLICATION_NAME: str = 'do2025-challenge'
    ADMIN_API_KEY: str
    CHALLENGE_NAME: str = 'DO2025'

    DEBUG: bool = False
    MONGO_HOST: str
    MONGO_USER: str
    MONGO_PASSWORD: str
    MONGO_TLS_CA_FILE: str = ""
    MONGO_TLS_CertificateKeyFile: str = ""
    MONGO_DATABASE_URI: Optional[MongoDsn] = None

    DATASETS_PATH: str

    SUBMISSION_LENGTH: int = 3000
    CHALLENGE_INITIAL_TOKENS: int = 100000
    CHALLENGE_BENCHMARKS: int = 3
    CORRECT_LABEL_PRICE: int = 1

    @validator("MONGO_DATABASE_URI", pre=True)
    def assemble_db_connection(cls, v: Optional[str], values: Dict[str, Any]) -> Any:
        if isinstance(v, str):
            return MongoDsn(v)
        return MongoDsn.build(
            scheme="mongodb",
            username=values.get("MONGO_USER"),
            password=values.get("MONGO_PASSWORD"),
            host=values.get("MONGO_HOST"),
        )

    @validator('BACKEND_CORS_ORIGINS', pre=True)
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> Union[List[str], str]:
        if isinstance(v, str) and not v.startswith('['):
            return [i.strip() for i in v.split(',')]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)

    class Config:
        case_sensitive = True


settings = Settings()
