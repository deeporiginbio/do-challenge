from pymongo import MongoClient

from app.config.core import settings
from app.config.core.logger import logger

mongo_client: MongoClient = None


def get_mongo_client():
    global mongo_client
    if mongo_client is None:
        mongo_db_uri = str(settings.MONGO_DATABASE_URI)
        if mongo_db_uri.startswith("mongodb+srv"):
            mongo_db_uri = mongo_db_uri.replace(":27017", "")

        if settings.MONGO_TLS_CA_FILE == "":
            logger.info({'message': 'Connecting to Mongo without TLS.'})
            mongo_client = MongoClient(
                mongo_db_uri,
                maxPoolSize=50,
                minPoolSize=4,
                uuidRepresentation="standard",
            )
        else:
            logger.info({'message': 'Connecting to Mongo using TLS.'})
            mongo_client = MongoClient(
                mongo_db_uri,
                maxPoolSize=10,
                minPoolSize=4,
                uuidRepresentation="standard",
                tls=True,
                tlsCAFile=settings.MONGO_TLS_CA_FILE,
                tlsCertificateKeyFile=settings.MONGO_TLS_CertificateKeyFile,
            )

    return mongo_client


def get_database():
    client = get_mongo_client()

    return client.do2025challenge


def create_indexes():
    db = get_database()
    db.teams.create_index("name", unique=True)
    db.challenges.create_index("title", unique=True)
    db.tasks.create_index(["team_id", "challenge_id"], unique=True)


def create_mongo_connection():
    mongo_client = get_mongo_client()

    try:
        mongo_client.admin.command('ping')
        create_indexes()

        logger.info({'message': 'Connected to mongo.'})
    except Exception as e:
        logger.exception(f'Could not connect to mongo: {e}')
        raise

    return mongo_client
