"""
GOLEX Backend - Cloudflare R2 Storage Client
S3-compatible object storage for images
"""

import boto3
import aioboto3
from botocore.exceptions import ClientError
from typing import Optional, BinaryIO
from app.config import settings
import logging
import mimetypes

logger = logging.getLogger(__name__)


class R2StorageClient:
    """Cloudflare R2 storage client (S3-compatible)"""
    
    def __init__(self):
        """Initialize R2 client"""
        self.session = aioboto3.Session()
        self.endpoint_url = settings.R2_ENDPOINT
        self.bucket_name = settings.R2_BUCKET_NAME
        self.public_url = settings.R2_PUBLIC_URL
        
        # Sync client for blocking operations
        self.sync_client = boto3.client(
            's3',
            endpoint_url=self.endpoint_url,
            aws_access_key_id=settings.R2_ACCESS_KEY_ID,
            aws_secret_access_key=settings.R2_SECRET_ACCESS_KEY,
            region_name='auto'  # R2 uses 'auto' region
        )
        
        logger.info(f"✅ R2 Storage Client initialized (bucket: {self.bucket_name})")
    
    async def upload_file(
        self,
        file_data: bytes,
        object_key: str,
        content_type: Optional[str] = None
    ) -> str:
        """
        Upload file to R2
        
        Args:
            file_data: File content as bytes
            object_key: S3 object key (e.g., "teams/123.png")
            content_type: MIME type (auto-detected if None)
        
        Returns:
            Public URL of uploaded file
        """
        try:
            # Auto-detect content type if not provided
            if not content_type:
                content_type, _ = mimetypes.guess_type(object_key)
                if not content_type:
                    content_type = 'application/octet-stream'
            
            async with self.session.client(
                's3',
                endpoint_url=self.endpoint_url,
                aws_access_key_id=settings.R2_ACCESS_KEY_ID,
                aws_secret_access_key=settings.R2_SECRET_ACCESS_KEY,
                region_name='auto'
            ) as s3:
                await s3.put_object(
                    Bucket=self.bucket_name,
                    Key=object_key,
                    Body=file_data,
                    ContentType=content_type,
                    CacheControl='public, max-age=31536000'  # 1 year cache
                )
            
            public_url = f"{self.public_url}/{object_key}"
            logger.info(f"✅ Uploaded: {object_key}")
            return public_url
            
        except ClientError as e:
            logger.error(f"❌ R2 upload failed: {e}")
            raise
    
    async def upload_from_url(
        self,
        url: str,
        object_key: str
    ) -> str:
        """
        Download from URL and upload to R2
        
        Args:
            url: Source URL (e.g., API-Football logo URL)
            object_key: R2 object key
        
        Returns:
            Public URL of uploaded file
        """
        import httpx
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(url)
                response.raise_for_status()
                
                content_type = response.headers.get('content-type')
                file_data = response.content
                
                return await self.upload_file(
                    file_data=file_data,
                    object_key=object_key,
                    content_type=content_type
                )
        except Exception as e:
            logger.error(f"❌ Download from URL failed ({url}): {e}")
            raise
    
    async def delete_file(self, object_key: str) -> bool:
        """Delete file from R2"""
        try:
            async with self.session.client(
                's3',
                endpoint_url=self.endpoint_url,
                aws_access_key_id=settings.R2_ACCESS_KEY_ID,
                aws_secret_access_key=settings.R2_SECRET_ACCESS_KEY,
                region_name='auto'
            ) as s3:
                await s3.delete_object(
                    Bucket=self.bucket_name,
                    Key=object_key
                )
            
            logger.info(f"🗑️ Deleted: {object_key}")
            return True
            
        except ClientError as e:
            logger.error(f"❌ R2 delete failed: {e}")
            return False
    
    async def file_exists(self, object_key: str) -> bool:
        """Check if file exists in R2"""
        try:
            async with self.session.client(
                's3',
                endpoint_url=self.endpoint_url,
                aws_access_key_id=settings.R2_ACCESS_KEY_ID,
                aws_secret_access_key=settings.R2_SECRET_ACCESS_KEY,
                region_name='auto'
            ) as s3:
                await s3.head_object(
                    Bucket=self.bucket_name,
                    Key=object_key
                )
            return True
        except ClientError:
            return False
    
    def get_public_url(self, object_key: str) -> str:
        """Get public URL for object"""
        return f"{self.public_url}/{object_key}"
    
    # ==========================================
    # HELPER METHODS
    # ==========================================
    
    async def upload_team_logo(self, team_id: str, logo_url: str) -> str:
        """Upload team logo from API-Football"""
        object_key = f"teams/{team_id}.png"
        
        # Check if already exists
        if await self.file_exists(object_key):
            logger.info(f"⏭️ Logo already exists: {team_id}")
            return self.get_public_url(object_key)
        
        # Download and upload
        return await self.upload_from_url(logo_url, object_key)
    
    async def upload_player_photo(self, player_id: str, photo_url: str) -> str:
        """Upload player photo from API-Football"""
        object_key = f"players/{player_id}.png"
        
        # Check if already exists
        if await self.file_exists(object_key):
            logger.info(f"⏭️ Photo already exists: {player_id}")
            return self.get_public_url(object_key)
        
        # Download and upload
        return await self.upload_from_url(photo_url, object_key)
    
    async def upload_league_logo(self, league_id: str, logo_url: str) -> str:
        """Upload league logo from API-Football"""
        object_key = f"leagues/{league_id}.png"
        
        if await self.file_exists(object_key):
            logger.info(f"⏭️ League logo already exists: {league_id}")
            return self.get_public_url(object_key)
        
        return await self.upload_from_url(logo_url, object_key)


# Global R2 client instance
r2_client = R2StorageClient()


# Convenience functions
def get_storage():
    """Dependency for FastAPI routes"""
    return r2_client

