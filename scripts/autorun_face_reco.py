# -*- coding: utf-8 -*-
import sys
import os
import click
import subprocess
import time
from watchdog.observers import Observer
from watchdog.events import PatternMatchingEventHandler
from shutil import copyfile
from share import upload_and_share

sys.path.insert(1, os.path.join(os.path.dirname(__file__), "../"))
from photo_face_reco import recognize

# This script listens to new faces to add in the model

OUTPUT_PATH = 'reco/'

class Params(object):
    def __init__(self, model, cozy_instance):
        Params.model = model
        Params.instance = cozy_instance

class Handler(PatternMatchingEventHandler):
    patterns=["*.jpg", "*.jpeg", "*.png"]

    def on_created(self, event):
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
        print("photo : %s" % event.src_path)
        print("model : %s" % Params.model)

        photo_basename = os.path.basename(event.src_path)
        photo_name = os.path.splitext(photo_basename)[0]
        out_dir = os.path.join(OUTPUT_PATH, photo_name)

        if not os.path.exists(out_dir):
            os.makedirs(out_dir)

        photo_copy_path = os.path.join(out_dir, photo_basename)
        # Copy the photo to be later uploaded
        copyfile(event.src_path, photo_copy_path)
        # Run the photo recognition
        recognize(photo_copy_path, Params.model, 0.53, out_dir, True)
        # Upload the photos and share the original ones with the reco persons
        upload_and_share(photo_name, out_dir, Params.instance)





@click.command()
@click.argument('photos_path')
@click.argument('model')
@click.option('--instance', default='cozy1.local:8080', help='Cozy instance')
def main(photos_path, model, instance):

    Params(model, instance)
    observer = Observer()
    observer.schedule(Handler(), path=photos_path)
    observer.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()

    observer.join()

if __name__ == "__main__":
    main()
