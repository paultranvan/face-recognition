# -*- coding: utf-8 -*-
import sys
import os
import click
import time
from watchdog.observers import Observer
from watchdog.events import PatternMatchingEventHandler

# This script listens to new faces to add in the model
sys.path.insert(1, os.path.join(os.path.dirname(__file__), "../"))
from photo_face_reco import recognize

class Model(object):
    def __init__(self, model):
        Model.model = model

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
        print("model : %s" % Model.model)
        recognize(event.src_path, Model.model, 0.53, 'reco', True)


@click.command()
@click.argument('photos_path')
@click.argument('model')
def main(photos_path, model):

    Model(model)
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
