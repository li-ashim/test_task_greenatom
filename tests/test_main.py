from tempfile import TemporaryFile

from fastapi import UploadFile
from fastapi.testclient import TestClient

from ..api.main import app

client = TestClient(app)


# All tests must be run with MinIO server up
class TestAPIEndpoints:
    """Tests api endpoints."""

    def _upload_files(self, num_files: int, content_type: str = 'image/jpg'):
        """
        Fixture-like making list of UploadFiles that can be used
        in requests' post method.
        """
        res = []
        for i in range(num_files):
            filename = f'im{i}.jpg'
            file = TemporaryFile()
            file.write(b'im%d_content' % i)
            upload_file = UploadFile(filename=filename,
                                     file=file,
                                     content_type=content_type)
            # requests needs no coroutines
            upload_file.read = upload_file.file.read
            # 'files' is `save_pictures` argument name
            res.append(('files', (filename, upload_file, content_type)))
        return res

    def test_save_pictures(self):
        upload_files = self._upload_files(3)
        response = client.post('/frames/', files=upload_files)
        assert response.status_code == 200
        # compare saved images names
        assert response.json()['saved_images'] \
            == list(map(lambda t: t[1][0], upload_files))

        upload_files = self._upload_files(16)
        response = client.post('/frames/', files=upload_files)
        assert response.status_code == 400

        upload_files = self._upload_files(1, 'image/png')
        response = client.post('/frames/', files=upload_files)
        assert response.status_code == 400

    def test_get_pictures(self):
        upload_files = self._upload_files(3)
        request_code = client.post(
            '/frames/',
            files=upload_files
        ).json()['request_code']
        response = client.get(f'/frames/{request_code}')
        assert response.status_code == 200
        assert len(response.json()) == len(upload_files)

    def test_delete_pictures(self):
        upload_files = self._upload_files(3)
        request_code = client.post(
            '/frames/',
            files=upload_files
        ).json()['request_code']
        response = client.delete(f'/frames/{request_code}')
        assert response.status_code == 200
