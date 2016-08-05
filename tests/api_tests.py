import unittest
import os
import shutil
import json
try: from urllib.parse import urlparse
except ImportError: from urlparse import urlparse # Py2 compatibility
from io import StringIO

import sys; print(list(sys.modules.keys()))
# Configure our app to use the testing databse
os.environ["CONFIG_PATH"] = "tuneful.config.TestingConfig"

from tuneful import app
from tuneful import models
from tuneful.utils import upload_path
from tuneful.database import Base, engine, session

class TestAPI(unittest.TestCase):
    """ Tests for the tuneful API """

    def setUp(self):
        """ Test setup """
        self.client = app.test_client()

        # Set up the tables in the database
        Base.metadata.create_all(engine)

        # Create folder for test uploads
        os.mkdir(upload_path())

    def tearDown(self):
        """ Test teardown """
        session.close()
        # Remove the tables and their data from the database
        Base.metadata.drop_all(engine)

        # Delete test upload folder
        shutil.rmtree(upload_path())

    def test_get_songs(self):
        """getting songs from database"""
        fileA = models.File(name="summertime.mp3")
        fileB = models.File(name="happy_birthday.mp3")
        songA = models.Song(file=fileA)
        songB = models.Song(file=fileB)
        session.add_all([songA, songB])
        session.commit()
        
        response = self.client.get("/api/songs",
            headers=[("Accept", "application/json")])
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.mimetype, "application/json")
        
        data = json.loads(response.data.decode("ascii"))
        #self.assertEqual(len(data), 2)
        
        songA = data[0]['file']['name']
        self.assertEqual(songA, "summertime.mp3")
        songB = data[1]['file']['name']
        self.assertEqual(songB, "happy_birthday.mp3")
        
        
