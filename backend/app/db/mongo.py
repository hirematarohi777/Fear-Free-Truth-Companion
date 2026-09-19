from typing import Optional
import pymongo
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from app.core.config import settings
from app.core.logging_config import logger


class DatabaseManager:
    client: Optional[AsyncIOMotorClient] = None
    db: Optional[AsyncIOMotorDatabase] = None

    @classmethod
    async def connect_to_database(cls, uri: Optional[str] = None, db_name: Optional[str] = None):
        target_uri = uri or settings.MONGODB_URI
        target_db = db_name or settings.MONGODB_DATABASE
        logger.info(f"Connecting to MongoDB at {target_uri}")
        cls.client = AsyncIOMotorClient(target_uri, serverSelectionTimeoutMS=5000)
        cls.db = cls.client[target_db]
        await cls.ensure_indexes()
        logger.info("MongoDB connected and indexes verified.")

    @classmethod
    async def close_database_connection(cls):
        if cls.client:
            cls.client.close()
            logger.info("MongoDB connection closed.")

    @classmethod
    async def ensure_indexes(cls):
        if cls.db is None:
            return

        # Users: unique normalized email
        await cls.db.users.create_index(
            [("emailNormalized", pymongo.ASCENDING)],
            unique=True,
            name="idx_users_email_unique"
        )

        # Sessions: unique token hash, TTL index on expiresAt
        await cls.db.sessions.create_index(
            [("tokenHash", pymongo.ASCENDING)],
            unique=True,
            name="idx_sessions_token_hash_unique"
        )
        await cls.db.sessions.create_index(
            [("expiresAt", pymongo.ASCENDING)],
            expireAfterSeconds=0,
            name="idx_sessions_ttl"
        )

        # Documents: ownerId and createdAt
        await cls.db.documents.create_index(
            [("ownerId", pymongo.ASCENDING), ("createdAt", pymongo.DESCENDING)],
            name="idx_documents_owner_created"
        )

        # Document Chunks: documentId and chunkIndex
        await cls.db.document_chunks.create_index(
            [("documentId", pymongo.ASCENDING), ("chunkIndex", pymongo.ASCENDING)],
            name="idx_document_chunks_lookup"
        )

        # Analyses: documentId and ownerId
        await cls.db.analyses.create_index(
            [("documentId", pymongo.ASCENDING), ("ownerId", pymongo.ASCENDING)],
            name="idx_analyses_doc_owner"
        )

        # URL Checks: ownerId and createdAt
        await cls.db.url_checks.create_index(
            [("ownerId", pymongo.ASCENDING), ("createdAt", pymongo.DESCENDING)],
            name="idx_url_checks_owner_created"
        )

        # Jobs: status and lease expiration for atomic queue polling
        await cls.db.jobs.create_index(
            [("status", pymongo.ASCENDING), ("leaseExpiresAt", pymongo.ASCENDING)],
            name="idx_jobs_queue_lease"
        )

        # Family invitations: token hash unique, recipient index
        await cls.db.family_invitations.create_index(
            [("tokenHash", pymongo.ASCENDING)],
            unique=True,
            name="idx_family_invitations_token_unique"
        )
        await cls.db.family_invitations.create_index(
            [("ownerId", pymongo.ASCENDING), ("reportId", pymongo.ASCENDING)],
            name="idx_family_invitations_owner_report"
        )

        # Report shares: recipientId and reportId compound, ownerId
        await cls.db.report_shares.create_index(
            [("recipientId", pymongo.ASCENDING), ("reportId", pymongo.ASCENDING)],
            name="idx_report_shares_recipient_report"
        )
        await cls.db.report_shares.create_index(
            [("ownerId", pymongo.ASCENDING)],
            name="idx_report_shares_owner"
        )

        # Audit events: actorId, resourceId, timestamp
        await cls.db.audit_events.create_index(
            [("actorId", pymongo.ASCENDING), ("timestamp", pymongo.DESCENDING)],
            name="idx_audit_actor_time"
        )
        await cls.db.audit_events.create_index(
            [("resourceId", pymongo.ASCENDING), ("timestamp", pymongo.DESCENDING)],
            name="idx_audit_resource_time"
        )


def get_db() -> AsyncIOMotorDatabase:
    if DatabaseManager.db is None:
        raise RuntimeError("Database not initialized")
    return DatabaseManager.db
