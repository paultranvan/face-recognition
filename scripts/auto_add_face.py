# -*- coding: utf-8 -*-
import sys
import os
import click
import time
from watchdog.observers import Observer
from watchdog.events import PatternMatchingEventHandler

sys.path.insert(1, os.path.join(os.path.dirname(__file__), "../"))
from model import add_face

# This script listens to new faces to add in the model


class Model(object):
    def __init__(self, model):
        Model.model = model

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

        add_face(event.src_path, Model.model)


@click.command()
@click.argument('faces_path')
@click.argument('model')
def main(faces_path, model):

    Model(model)
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
