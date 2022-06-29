"""
Data storage utility.
"""
import base64
import os
from datetime import date, datetime
from uuid import uuid4

from fastapi import HTTPException, UploadFile
from minio import Minio
from minio.deleteobjects import DeleteObject
from pydantic import BaseModel

from .db_utils import DBManager


class MinioClientManager:
    """Manager class for minio client object."""
    _client: Minio | None = None

    @classmethod
    def initialize(cls,
                   endpoint: str = '127.0.0.1:9000',
                   access_key: str = 'minioadmin',
                   secret_key: str = 'minioadmin',
                   secure: bool = False) -> Minio:
        cls._client = Minio(endpoint=endpoint,
                            access_key=access_key,
                            secret_key=secret_key,
                            secure=secure)
        return cls._client

    @classmethod
    def get_client(cls):
        return cls._client


class Image(BaseModel):
    """Model representing base64 encoded image and its info."""
    name: str
    saved_on: str
    base64_encoded_content: bytes

    def __init__(__pydantic_self__, *, name: str, saved_on: str,
                 base64_encoded_content: bytes, **data) -> None:
        super().__init__(
            name=name, saved_on=saved_on,
            base64_encoded_content=base64_encoded_content,
            **data
        )


def save_images(images: list[UploadFile]) -> tuple[str, list[str]]:
    """
    Save images into bucket in MinIO, add information about
    them in database and return request code and list of saved images names.
    """
    bucket_name = date.today().strftime('%Y%m%d')  # i.e. YYYYMMDD
    client = MinioClientManager.get_client()
    if not client.bucket_exists(bucket_name):
        client.make_bucket(bucket_name)

    request_code = str(uuid4())
    saved_images = []
    for image in images:
        image_name = str(uuid4()) + '.jpg'
        length = os.fstat(image.file.fileno()).st_size
        client.put_object(bucket_name, image_name, image.file,
                          length, content_type='image/jpeg')
        DBManager.save_to_db(request_code,
                             image_name,
                             datetime.now().isoformat())
        saved_images.append(image.filename)

    return request_code, saved_images


def get_images(request_code: str) -> list[Image]:
    """Return base64 encoded images and information about them."""
    try:
        bucket_name = DBManager.get_bucket_name(request_code)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f'Incorrect request code: {request_code}'
        )
    else:
        res = []
        images_info = DBManager.get_images_info(request_code)
        client = MinioClientManager.get_client()
        for image_name, saved_on in images_info:
            base64_encoded_content = base64.b64encode(
                client.get_object(bucket_name, image_name).read()
            )
            res.append(Image(name=image_name, saved_on=saved_on,
                             base64_encoded_content=base64_encoded_content))
        return res


def delete_images(request_code: str) -> str:
    try:
        bucket_name = DBManager.get_bucket_name(request_code)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f'There is no images with request code: {request_code}'
        )
    else:
        # mypy swears at lambdas with more than one argument
        images_to_delete = map(
            lambda name, _: DeleteObject(name),  # type: ignore
            DBManager.get_images_info(request_code)
        )
        DBManager.delete_images_info(request_code)
        MinioClientManager.get_client().remove_objects(
            bucket_name, images_to_delete
        )
        return f'Images from {request_code} request were successfully deleted.'
