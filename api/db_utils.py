"""
Sqlite interaction utility.
"""
import sqlite3
from datetime import datetime


class DBManager:
    """Sqlite database manager."""
    _con: sqlite3.Connection
    _cur: sqlite3.Cursor

    @classmethod
    def initialize(cls, db_name: str = 'test.db',
                   check_same_thread: bool = False):
        """Establish connection to database and create cursor object."""
        cls. _con = sqlite3.connect(
            db_name, check_same_thread=check_same_thread
        )
        cls._cur = cls._con.cursor()
        return cls

    @classmethod
    def create_table(cls):
        """Create database."""
        cls._cur.execute('''
            CREATE TABLE IF NOT EXISTS inbox (
            id INTEGER PRIMARY KEY,
            request_code TEXT,
            image_name TEXT,
            saved_on TEXT);
        ''')

    @classmethod
    def save_to_db(cls, request_code: str,
                   image_name: str, saved_on: str) -> None:
        """Insert one entry into table."""
        cls._cur.execute('''
            INSERT INTO inbox (request_code, image_name, saved_on)
            values (?, ?, ?);
        ''', (request_code, image_name, saved_on))
        cls._con.commit()

    @classmethod
    def get_bucket_name(cls, request_code: str) -> str:
        """
        Return name of bucket as formated date of
        first image in request.
        """
        cls._cur.execute('''
            SELECT saved_on
            FROM inbox
            WHERE request_code = (?)
            ORDER BY saved_on
            LIMIT 1;
        ''', (request_code,))
        first_img_request_date = cls._cur.fetchone()
        if first_img_request_date:
            bucket_name = datetime.fromisoformat(
                first_img_request_date[0]
            ).strftime('%Y%m%d')
            return bucket_name
        raise ValueError

    @classmethod
    def get_images_info(cls, request_code: str) -> list[tuple[str, str]]:
        """Get image's name and save datetime."""
        cls._cur.execute('''
            SELECT image_name, saved_on
            FROM inbox
            WHERE request_code = (?);
        ''', (request_code,))
        return cls._cur.fetchall()

    @classmethod
    def delete_images_info(cls, request_code: str) -> None:
        """Delete information about images with given request code."""
        cls._cur.execute('''
            DELETE FROM inbox
            WHERE request_code = (?);
        ''', (request_code,))
        cls._con.commit()
