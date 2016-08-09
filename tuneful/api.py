import os.path
import json

from flask import request, Response, url_for, send_from_directory
from werkzeug.utils import secure_filename
from jsonschema import validate, ValidationError

from . import models
from . import decorators
from tuneful import app
from .database import session
from .utils import upload_path

post_schema = {
    "properties": {
                "file": {"type": "object",
                "properties": {"id": {"type": "number"}
                    },
                "required": ["id"]
                }
            },
    "required": ["file"]
            }

@app.route("/api/songs", methods=["GET"])
@decorators.accept("application/json")
def songs_get():
    songs = session.query(models.Song)
    data = json.dumps([song.as_dictionary() for song in songs])
    return Response(data, 200, mimetype="application/json")
    
    
@app.route("/api/songs", methods=["POST"])
@decorators.accept("application/json")
@decorators.require("application/json")
def add_song():
    data = request.json
    print(data)
    # Check that the JSON supplied is valid
    # If not you return a 422 Unprocessable Entity
    try:
        validate(data, post_schema)
    except ValidationError as error:
        data = {"message": error.message}
        return Response(json.dumps(data), 401, mimetype="application/json")
    
    file = session.query(models.File).get(data["file"]["id"])
    song = models.Song(file=file)
    session.add(song)
    session.commit()
    
    data = json.dumps(song.as_dictionary())
    headers = {"Location": url_for("songs_get")}
    #print(headers)
    return Response(data, 201, headers=headers, mimetype="application/json")
    
@app.route("/api/songs/<int:id>", methods=["DELETE"])
@decorators.accept("application/json")
def song_delete(id):
    """delete song from database"""
    song = session.query(models.Song).get(id)
    file = song.file

    # check if song exists
    if not song:
        message = "There is no song with id {}.".format(id)
        data = json.dumps({"message": message})
        return Response(data, 404, mimetype="application/json")

    session.delete(song)
    session.delete(file)
    session.commit()

    songs = session.query(models.Song).all()

    # return info after deletion
    data = json.dumps([song.as_dictionary() for song in songs])
    return Response(data, 200, mimetype="application/json")
    
@app.route("/api/songs/<int:id>", methods=["PUT"])
@decorators.accept("application/json")
def song_edit(id):
    """ edit an existing song """
    data = request.json
    
    # get file & song from database
    song = session.query(models.Song).get(id)
    file = song.file
    
    # edit the file name in the database
    file.name = data["name"]
    session.commit()

    # setting correct headers for song
    data = json.dumps(song.as_dictionary())
    headers = {"Location": url_for("songs_get")}
    return Response(data, 201, headers=headers, mimetype="application/json")

@app.route("/uploads/<filename>", methods=["GET"])
def uploaded_file(filename):
    return send_from_directory(upload_path(), filename)
    
@app.route("/api/files", methods=["POST"])
@decorators.require("multipart/form-data")
@decorators.accept("application/json")
def file_post():
    file = request.files.get("file")
    if not file:
        data = {"message": "Could not find file data"}
        return Response(json.dumps(data), 422, mimetype="application/json")

    filename = secure_filename(file.filename)
    db_file = models.File(name=filename)
    db_song = models.Song(file=db_file)
    session.add_all([db_file,db_song])    
    session.commit()
    file.save(upload_path(filename))

    data = db_file.as_dictionary()
    return Response(json.dumps(data), 201, mimetype="application/json")
    
