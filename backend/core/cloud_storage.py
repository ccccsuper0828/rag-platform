"""
云存储统一接口模块

支持多种存储后端：
- local: 本地文件系统（开发环境）
- s3: AWS S3 / MinIO
- oss: 阿里云 OSS
- cos: 腾讯云 COS

生产环境推荐使用云存储，实现：
1. 多租户文件隔离
2. 高可用和冗余
3. CDN 加速
4. 自动备份
"""

import os
import io
import hashlib
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, BinaryIO, Union
from abc import ABC, abstractmethod
import logging

# 加载环境变量
from dotenv import load_dotenv
load_dotenv()

logger = logging.getLogger(__name__)

# 存储配置
STORAGE_TYPE = os.getenv("STORAGE_TYPE", "local")  # local, s3, oss, cos
LOCAL_STORAGE_PATH = Path(os.getenv("LOCAL_STORAGE_PATH", "user_data"))

# S3 配置
S3_ENDPOINT = os.getenv("S3_ENDPOINT", "")  # 留空使用 AWS，填写则使用 MinIO
S3_ACCESS_KEY = os.getenv("S3_ACCESS_KEY", "")
S3_SECRET_KEY = os.getenv("S3_SECRET_KEY", "")
S3_BUCKET = os.getenv("S3_BUCKET", "rag-platform")
S3_REGION = os.getenv("S3_REGION", "us-east-1")

# OSS 配置
OSS_ENDPOINT = os.getenv("OSS_ENDPOINT", "")
OSS_ACCESS_KEY = os.getenv("OSS_ACCESS_KEY", "")
OSS_SECRET_KEY = os.getenv("OSS_SECRET_KEY", "")
OSS_BUCKET = os.getenv("OSS_BUCKET", "rag-platform")

# COS 配置
COS_REGION = os.getenv("COS_REGION", "")
COS_SECRET_ID = os.getenv("COS_SECRET_ID", "")
COS_SECRET_KEY = os.getenv("COS_SECRET_KEY", "")
COS_BUCKET = os.getenv("COS_BUCKET", "rag-platform")


class StorageBackend(ABC):
    """存储后端抽象基类"""
    
    @abstractmethod
    def upload(self, user_id: str, filename: str, content: Union[bytes, BinaryIO]) -> str:
        """上传文件，返回存储路径/URL"""
        pass
    
    @abstractmethod
    def download(self, path: str) -> bytes:
        """下载文件内容"""
        pass
    
    @abstractmethod
    def delete(self, path: str) -> bool:
        """删除文件"""
        pass
    
    @abstractmethod
    def exists(self, path: str) -> bool:
        """检查文件是否存在"""
        pass
    
    @abstractmethod
    def get_url(self, path: str, expires_in: int = 3600) -> str:
        """获取文件访问 URL（可能是签名 URL）"""
        pass
    
    @abstractmethod
    def list_files(self, user_id: str, prefix: str = "") -> list:
        """列出用户的文件"""
        pass


class LocalStorage(StorageBackend):
    """本地文件存储（开发环境）"""
    
    def __init__(self, base_path: Path = LOCAL_STORAGE_PATH):
        self.base_path = base_path
        self.base_path.mkdir(parents=True, exist_ok=True)
    
    def _get_user_path(self, user_id: str) -> Path:
        user_path = self.base_path / user_id / "uploads"
        user_path.mkdir(parents=True, exist_ok=True)
        return user_path
    
    def _generate_filename(self, filename: str) -> str:
        """生成唯一文件名"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        name, ext = os.path.splitext(filename)
        hash_suffix = hashlib.md5(f"{name}{timestamp}".encode()).hexdigest()[:8]
        return f"{name}_{timestamp}_{hash_suffix}{ext}"
    
    def upload(self, user_id: str, filename: str, content: Union[bytes, BinaryIO]) -> str:
        user_path = self._get_user_path(user_id)
        safe_filename = self._generate_filename(filename)
        file_path = user_path / safe_filename
        
        if isinstance(content, bytes):
            file_path.write_bytes(content)
        else:
            with open(file_path, "wb") as f:
                f.write(content.read())
        
        # 返回相对路径
        return str(file_path.relative_to(self.base_path.parent))
    
    def download(self, path: str) -> bytes:
        full_path = self.base_path.parent / path
        if full_path.exists():
            return full_path.read_bytes()
        raise FileNotFoundError(f"File not found: {path}")
    
    def delete(self, path: str) -> bool:
        full_path = self.base_path.parent / path
        if full_path.exists():
            full_path.unlink()
            return True
        return False
    
    def exists(self, path: str) -> bool:
        full_path = self.base_path.parent / path
        return full_path.exists()
    
    def get_url(self, path: str, expires_in: int = 3600) -> str:
        # 本地存储返回相对路径，由 API 处理
        return f"/api/files/{path}"
    
    def list_files(self, user_id: str, prefix: str = "") -> list:
        user_path = self._get_user_path(user_id)
        files = []
        for f in user_path.iterdir():
            if f.is_file() and (not prefix or f.name.startswith(prefix)):
                files.append({
                    "name": f.name,
                    "path": str(f.relative_to(self.base_path.parent)),
                    "size": f.stat().st_size,
                    "modified": datetime.fromtimestamp(f.stat().st_mtime).isoformat()
                })
        return files


class S3Storage(StorageBackend):
    """AWS S3 / MinIO 存储"""
    
    def __init__(self):
        try:
            import boto3
            from botocore.config import Config
        except ImportError:
            raise ImportError("请安装 boto3: pip install boto3")
        
        config = Config(
            signature_version='s3v4',
            s3={'addressing_style': 'path'}
        )
        
        if S3_ENDPOINT:
            # MinIO 或自建 S3
            self.client = boto3.client(
                's3',
                endpoint_url=S3_ENDPOINT,
                aws_access_key_id=S3_ACCESS_KEY,
                aws_secret_access_key=S3_SECRET_KEY,
                config=config
            )
        else:
            # AWS S3
            self.client = boto3.client(
                's3',
                region_name=S3_REGION,
                aws_access_key_id=S3_ACCESS_KEY,
                aws_secret_access_key=S3_SECRET_KEY,
                config=config
            )
        
        self.bucket = S3_BUCKET
        self._ensure_bucket()
    
    def _ensure_bucket(self):
        """确保 bucket 存在"""
        try:
            self.client.head_bucket(Bucket=self.bucket)
        except:
            try:
                self.client.create_bucket(Bucket=self.bucket)
                logger.info(f"Created S3 bucket: {self.bucket}")
            except Exception as e:
                logger.warning(f"Could not create bucket: {e}")
    
    def _get_key(self, user_id: str, filename: str) -> str:
        """生成 S3 对象键"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        name, ext = os.path.splitext(filename)
        hash_suffix = hashlib.md5(f"{name}{timestamp}".encode()).hexdigest()[:8]
        return f"users/{user_id}/uploads/{name}_{timestamp}_{hash_suffix}{ext}"
    
    def upload(self, user_id: str, filename: str, content: Union[bytes, BinaryIO]) -> str:
        key = self._get_key(user_id, filename)
        
        if isinstance(content, bytes):
            self.client.put_object(Bucket=self.bucket, Key=key, Body=content)
        else:
            self.client.upload_fileobj(content, self.bucket, key)
        
        return f"s3://{self.bucket}/{key}"
    
    def download(self, path: str) -> bytes:
        # 解析 s3:// URL 或直接使用 key
        if path.startswith("s3://"):
            path = path.replace(f"s3://{self.bucket}/", "")
        
        response = self.client.get_object(Bucket=self.bucket, Key=path)
        return response['Body'].read()
    
    def delete(self, path: str) -> bool:
        if path.startswith("s3://"):
            path = path.replace(f"s3://{self.bucket}/", "")
        try:
            self.client.delete_object(Bucket=self.bucket, Key=path)
            return True
        except:
            return False
    
    def exists(self, path: str) -> bool:
        if path.startswith("s3://"):
            path = path.replace(f"s3://{self.bucket}/", "")
        try:
            self.client.head_object(Bucket=self.bucket, Key=path)
            return True
        except:
            return False
    
    def get_url(self, path: str, expires_in: int = 3600) -> str:
        if path.startswith("s3://"):
            path = path.replace(f"s3://{self.bucket}/", "")
        
        url = self.client.generate_presigned_url(
            'get_object',
            Params={'Bucket': self.bucket, 'Key': path},
            ExpiresIn=expires_in
        )
        return url
    
    def list_files(self, user_id: str, prefix: str = "") -> list:
        search_prefix = f"users/{user_id}/uploads/{prefix}"
        response = self.client.list_objects_v2(
            Bucket=self.bucket,
            Prefix=search_prefix
        )
        
        files = []
        for obj in response.get('Contents', []):
            files.append({
                "name": obj['Key'].split('/')[-1],
                "path": f"s3://{self.bucket}/{obj['Key']}",
                "size": obj['Size'],
                "modified": obj['LastModified'].isoformat()
            })
        return files


class OSSStorage(StorageBackend):
    """阿里云 OSS 存储"""
    
    def __init__(self):
        try:
            import oss2
        except ImportError:
            raise ImportError("请安装 oss2: pip install oss2")
        
        self.auth = oss2.Auth(OSS_ACCESS_KEY, OSS_SECRET_KEY)
        self.bucket = oss2.Bucket(self.auth, OSS_ENDPOINT, OSS_BUCKET)
        self.bucket_name = OSS_BUCKET
    
    def _get_key(self, user_id: str, filename: str) -> str:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        name, ext = os.path.splitext(filename)
        hash_suffix = hashlib.md5(f"{name}{timestamp}".encode()).hexdigest()[:8]
        return f"users/{user_id}/uploads/{name}_{timestamp}_{hash_suffix}{ext}"
    
    def upload(self, user_id: str, filename: str, content: Union[bytes, BinaryIO]) -> str:
        key = self._get_key(user_id, filename)
        
        if isinstance(content, bytes):
            self.bucket.put_object(key, content)
        else:
            self.bucket.put_object(key, content)
        
        return f"oss://{self.bucket_name}/{key}"
    
    def download(self, path: str) -> bytes:
        if path.startswith("oss://"):
            path = path.replace(f"oss://{self.bucket_name}/", "")
        
        result = self.bucket.get_object(path)
        return result.read()
    
    def delete(self, path: str) -> bool:
        if path.startswith("oss://"):
            path = path.replace(f"oss://{self.bucket_name}/", "")
        try:
            self.bucket.delete_object(path)
            return True
        except:
            return False
    
    def exists(self, path: str) -> bool:
        if path.startswith("oss://"):
            path = path.replace(f"oss://{self.bucket_name}/", "")
        return self.bucket.object_exists(path)
    
    def get_url(self, path: str, expires_in: int = 3600) -> str:
        if path.startswith("oss://"):
            path = path.replace(f"oss://{self.bucket_name}/", "")
        return self.bucket.sign_url('GET', path, expires_in)
    
    def list_files(self, user_id: str, prefix: str = "") -> list:
        import oss2
        search_prefix = f"users/{user_id}/uploads/{prefix}"
        
        files = []
        for obj in oss2.ObjectIterator(self.bucket, prefix=search_prefix):
            files.append({
                "name": obj.key.split('/')[-1],
                "path": f"oss://{self.bucket_name}/{obj.key}",
                "size": obj.size,
                "modified": obj.last_modified
            })
        return files


class COSStorage(StorageBackend):
    """腾讯云 COS 存储"""
    
    def __init__(self):
        try:
            from qcloud_cos import CosConfig, CosS3Client
        except ImportError:
            raise ImportError("请安装 cos-python-sdk-v5: pip install cos-python-sdk-v5")
        
        config = CosConfig(
            Region=COS_REGION,
            SecretId=COS_SECRET_ID,
            SecretKey=COS_SECRET_KEY
        )
        self.client = CosS3Client(config)
        self.bucket = COS_BUCKET
    
    def _get_key(self, user_id: str, filename: str) -> str:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        name, ext = os.path.splitext(filename)
        hash_suffix = hashlib.md5(f"{name}{timestamp}".encode()).hexdigest()[:8]
        return f"users/{user_id}/uploads/{name}_{timestamp}_{hash_suffix}{ext}"
    
    def upload(self, user_id: str, filename: str, content: Union[bytes, BinaryIO]) -> str:
        key = self._get_key(user_id, filename)
        
        if isinstance(content, bytes):
            self.client.put_object(Bucket=self.bucket, Key=key, Body=content)
        else:
            self.client.put_object(Bucket=self.bucket, Key=key, Body=content.read())
        
        return f"cos://{self.bucket}/{key}"
    
    def download(self, path: str) -> bytes:
        if path.startswith("cos://"):
            path = path.replace(f"cos://{self.bucket}/", "")
        
        response = self.client.get_object(Bucket=self.bucket, Key=path)
        return response['Body'].get_raw_stream().read()
    
    def delete(self, path: str) -> bool:
        if path.startswith("cos://"):
            path = path.replace(f"cos://{self.bucket}/", "")
        try:
            self.client.delete_object(Bucket=self.bucket, Key=path)
            return True
        except:
            return False
    
    def exists(self, path: str) -> bool:
        if path.startswith("cos://"):
            path = path.replace(f"cos://{self.bucket}/", "")
        try:
            self.client.head_object(Bucket=self.bucket, Key=path)
            return True
        except:
            return False
    
    def get_url(self, path: str, expires_in: int = 3600) -> str:
        if path.startswith("cos://"):
            path = path.replace(f"cos://{self.bucket}/", "")
        return self.client.get_presigned_url(
            Method='GET',
            Bucket=self.bucket,
            Key=path,
            Expired=expires_in
        )
    
    def list_files(self, user_id: str, prefix: str = "") -> list:
        search_prefix = f"users/{user_id}/uploads/{prefix}"
        response = self.client.list_objects(Bucket=self.bucket, Prefix=search_prefix)
        
        files = []
        for obj in response.get('Contents', []):
            files.append({
                "name": obj['Key'].split('/')[-1],
                "path": f"cos://{self.bucket}/{obj['Key']}",
                "size": obj['Size'],
                "modified": obj['LastModified']
            })
        return files


# ============================================================
# 统一存储接口
# ============================================================

_storage_instance: Optional[StorageBackend] = None


def get_storage() -> StorageBackend:
    """获取存储后端实例（单例）"""
    global _storage_instance
    
    if _storage_instance is None:
        storage_type = STORAGE_TYPE.lower()
        
        if storage_type == "s3":
            _storage_instance = S3Storage()
            logger.info("Using S3 storage backend")
        elif storage_type == "oss":
            _storage_instance = OSSStorage()
            logger.info("Using Aliyun OSS storage backend")
        elif storage_type == "cos":
            _storage_instance = COSStorage()
            logger.info("Using Tencent COS storage backend")
        else:
            _storage_instance = LocalStorage()
            logger.info("Using local storage backend")
    
    return _storage_instance


class CloudStorage:
    """
    统一云存储接口类
    
    使用示例：
    ```python
    from core.cloud_storage import CloudStorage
    
    storage = CloudStorage()
    
    # 上传文件
    path = storage.upload(user_id="user123", filename="doc.pdf", content=file_bytes)
    
    # 获取访问 URL
    url = storage.get_url(path)
    
    # 下载文件
    content = storage.download(path)
    
    # 列出用户文件
    files = storage.list_files(user_id="user123")
    ```
    """
    
    def __init__(self):
        self._backend = get_storage()
    
    def upload(self, user_id: str, filename: str, content: Union[bytes, BinaryIO]) -> str:
        """
        上传文件
        
        Args:
            user_id: 用户 ID
            filename: 原始文件名
            content: 文件内容（bytes 或 file-like 对象）
        
        Returns:
            存储路径/URL
        """
        return self._backend.upload(user_id, filename, content)
    
    def download(self, path: str) -> bytes:
        """下载文件内容"""
        return self._backend.download(path)
    
    def delete(self, path: str) -> bool:
        """删除文件"""
        return self._backend.delete(path)
    
    def exists(self, path: str) -> bool:
        """检查文件是否存在"""
        return self._backend.exists(path)
    
    def get_url(self, path: str, expires_in: int = 3600) -> str:
        """获取文件访问 URL"""
        return self._backend.get_url(path, expires_in)
    
    def list_files(self, user_id: str, prefix: str = "") -> list:
        """列出用户的文件"""
        return self._backend.list_files(user_id, prefix)
    
    @property
    def backend_type(self) -> str:
        """获取当前存储后端类型"""
        return STORAGE_TYPE


# 便捷函数
def upload_file(user_id: str, filename: str, content: Union[bytes, BinaryIO]) -> str:
    """上传文件的便捷函数"""
    return get_storage().upload(user_id, filename, content)


def download_file(path: str) -> bytes:
    """下载文件的便捷函数"""
    return get_storage().download(path)


def get_file_url(path: str, expires_in: int = 3600) -> str:
    """获取文件 URL 的便捷函数"""
    return get_storage().get_url(path, expires_in)

