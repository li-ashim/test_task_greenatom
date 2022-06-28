from datetime import datetime, timedelta

import pytest

from ..api.db_utils import DBManager


class TestDBManager:
    """Tests DBManager functionality."""
    dbm = DBManager.initialize(':memory:')
    request_code = 'test_request_code'
    saved_on = datetime.now()
    dt = timedelta(seconds=1)
    data = [(request_code, 'im1.jpg', saved_on.isoformat()),
            (request_code, 'im2.jpg', (saved_on+dt).isoformat())]

    def test_create_table(self):
        self.dbm.create_table()
        check_table_exist_query = '''
            SELECT name
            FROM sqlite_master
            WHERE type="table" AND name="inbox";
        '''
        assert self.dbm._cur.execute(check_table_exist_query).fetchall()

    def test_save_to_db(self):
        select_query = f'''
            SELECT request_code, image_name, saved_on
            FROM inbox
            WHERE request_code = "{self.request_code}";
        '''
        for items in self.data:
            self.dbm.save_to_db(*items)
        assert list(
            self.dbm._cur.execute(select_query).fetchall()
            ) == self.data

    def test_get_bucket_name(self):
        bucket_name = self.saved_on.strftime('%Y%m%d')
        assert self.dbm.get_bucket_name(self.request_code) == bucket_name
        with pytest.raises(ValueError):
            self.dbm.get_bucket_name('NOT_PROPER_REQUEST_CODE')

    def test_delete_images_info(self):
        select_query = f'''
            SELECT request_code, image_name, saved_on
            FROM inbox
            WHERE request_code = "{self.request_code}";
        '''
        assert len(self.dbm._cur.execute(select_query).fetchall()) == 2
        self.dbm.delete_images_info(self.request_code)
        assert len(self.dbm._cur.execute(select_query).fetchall()) == 0

    def test_get_images_info(self):
        for items in self.data:
            self.dbm.save_to_db(*items)
        images_info = self.dbm.get_images_info(self.request_code)
        assert len(images_info) == 2
        assert images_info[0][0] == self.data[0][1]  # compare names
