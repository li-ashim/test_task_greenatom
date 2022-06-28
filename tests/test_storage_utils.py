from datetime import datetime
from tempfile import TemporaryFile

import pytest
from fastapi import HTTPException, UploadFile

from ..api.db_utils import DBManager
from ..api.storage_utils import (
    MinioClientManager, delete_images, get_images, save_images)


# All tests must be run with MinIO server up
class TestStorageOperations:
    """Tests storage interaction function."""
    minio_client = MinioClientManager.initialize()
    dbm = DBManager.initialize(':memory:')
    dbm.create_table()

    @pytest.fixture
    def upload_files(self):
        file1 = TemporaryFile()
        file1.write(b'im1_content')
        file2 = TemporaryFile()
        file2.write(b'im2_content')
        return [
            UploadFile('im1.jpg', file1),
            UploadFile('im2.jpg', file2)
        ]

    def test_save_images(self, upload_files):
        bucket_name = datetime.now().date().strftime('%Y%m%d')
        request_code, saved_images = save_images(upload_files)
        image_storage_names = list(map(lambda info_tuple: info_tuple[0],
                                       self.dbm.get_images_info(request_code)))
        assert self.minio_client.bucket_exists(bucket_name)
        assert list(map(lambda uf: uf.filename, upload_files)) == saved_images
        for i in range(len(upload_files)):
            assert self.minio_client.get_object(
                bucket_name, image_storage_names[i]
            ).read() == upload_files[i].file.read()

    def test_get_images(self, upload_files):
        request_code, _ = save_images(upload_files)
        images = get_images(request_code)
        with pytest.raises(HTTPException):
            get_images('NOT_PROPER_REQUEST_CODE')
        assert len(upload_files) == len(images)

    def test_delete_images(self, upload_files):
        request_code, _ = save_images(upload_files)
        images = get_images(request_code)
        assert len(upload_files) == len(images)

        delete_images(request_code)
        with pytest.raises(HTTPException):
            get_images(request_code)
