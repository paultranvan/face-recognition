# -*- coding: utf-8 -*-
import sys
import os
import click
import time
import json
from stat import S_ISREG, ST_CTIME, ST_MODE
from watchdog.observers import Observer
from watchdog.events import PatternMatchingEventHandler

sys.path.insert(1, os.path.join(os.path.dirname(__file__), "../"))
from model import add_face
from photo_face_reco import recognize
from photo_face_reco import image_files_in_folder
from share import upload_and_share
from share import remote_face_copy

# This script listens to new faces to add in the model


def list_dir_by_date(dir_path):
    dirs = (os.path.join(dir_path, fn) for fn in os.listdir(dir_path) if os.path.isdir(os.path.join(dir_path, fn)))
    dirs = ((os.stat(path), path) for path in dirs)
    dirs = ((stat[ST_CTIME], path) for stat, path in dirs)

    sorted_dirs = [path for time, path in sorted(dirs, reverse=True)]
    return sorted_dirs

def count_unknown(dir_path):
    cpt = 0
    for fn in os.listdir(dir_path):
        file_path = os.path.join(dir_path, fn)
        ext = os.path.splitext(file_path)[1]
        if ext == ".json":
            with open(file_path) as f:
                data = json.load(f)
                subjects = data['subjects']
                for s in subjects:
                    if s == "unknown":
                        cpt = cpt + 1
    return cpt


def get_photo_path_in_dir(dir_path):
    imgs = image_files_in_folder(dir_path)
    for img in imgs:
        if "_reco" not in img:
            return img


class Params(object):
    def __init__(self, model, reco_path, instance, remote_server):
        Params.model = model
        Params.reco_path = reco_path
        Params.instance = instance
        Params.remote_server = remote_server

class Handler(PatternMatchingEventHandler):
    patterns=["*.jpg"]

    def on_created(self, event):
        # Do something here, like face reco
        self.process(event)

    def process(self, event):
        """
        event.event_type
            'modified' | 'created' | 'moved' | 'deleted'
        event.is_directory
            True | False
        event.src_path
            path/to/observed/file
        """

        add_face(event.src_path, Params.model)
        print("src path %s" % event.src_path)
        remote_face_copy(event.src_path, Params.instance, Params.remote_server )

        # Let's check photos with the updated model
        if Params.reco_path != "":
            dirs = list_dir_by_date(Params.reco_path)
            photo_face_basename = os.path.basename(event.src_path)

            for d in dirs:
                print("check dir %s with this new face" % d)
                n_unknown = count_unknown(d)
                if n_unknown > 0:
                    photo_path = get_photo_path_in_dir(d)
                    photo_name = os.path.splitext(os.path.basename(photo_path))[0]

                    recognize(photo_path, Params.model, 0.53, Params.reco_path, True)
                    print('photo name : %s' % photo_name)
                    upload_and_share(photo_name, d, Params.instance, Params.remote_server)


@click.command()
@click.argument('faces_path')
@click.argument('model')
@click.option('--reco_path', default='', help='Path of the photo directory on which running the recognition. No path means no reco.')
@click.option('--instance', default='cozy1.local:8080', help='Cozy instance')
@click.option('--remote_server', default='', help='Remote server <user>@<server_host>')
def main(faces_path, model, reco_path, instance, remote_server):

    Params(model, reco_path, instance, remote_server)
    observer = Observer()
    observer.schedule(Handler(), path=faces_path)
    observer.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()

    observer.join()

if __name__ == "__main__":
    main()
