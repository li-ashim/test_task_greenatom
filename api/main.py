from fastapi import FastAPI, HTTPException, UploadFile
from pydantic import BaseModel

from .db_utils import DBManager
from .storage_utils import (Image, MinioClientManager, delete_images,
                            get_images, save_images)

MinioClientManager.initialize()
DBManager.initialize()
DBManager.create_table()

description = '''
This api helps to save packs of images.
## Restrictions:
* Each pack can contain no more than 15 images
* Only jpeg/jpg images supported
'''
app = FastAPI(
    title='ImagePacks',
    description=description
)


def _is_jpeg_image(file: UploadFile) -> bool:
    """Tell wheather file is of type jpg/jpeg."""
    if file.content_type in {'image/jpg', 'image/jpeg'}:
        return True
    return False


class PostResponseModel(BaseModel):
    request_code: str
    saved_images: list[str]


@app.post('/frames/', response_model=PostResponseModel)
def save_pictures(files: list[UploadFile]):
    """
    Save pack of images.

    Save pack of images in object storage and
    fixate information about each image in database.
    Return request code of pack and names of saved images.
    """
    if len(files) > 15:
        print("Too long")
        raise HTTPException(
            status_code=400,
            detail="Too many images uploaded."
        )
    if not all(map(_is_jpeg_image, files)):
        raise HTTPException(
            status_code=400,
            detail="Jpeg image format is expected."
        )

    request_code, saved_images = save_images(files)
    return {'request_code': request_code, 'saved_images': saved_images}


@app.get('/frames/{request_code}', response_model=list[Image])
def get_pictures(request_code: str):
    """Get pictures from pack with given request code."""
    return get_images(request_code)


@app.delete('/frames/{request_code}')
def delete_pictures(request_code: str):
    """Delete pictures from pack with given request code."""
    message = delete_images(request_code)
    return {'message': message}
