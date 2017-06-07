# -*- coding: utf-8 -*-
from __future__ import print_function
from PIL import Image, ImageDraw
import click
import os
import re
import scipy.misc
import warnings
import pickle
import face_recognition.api as face_recognition

MODEL_FILE = "model.pkl"


def show_model(model):
    with open(MODEL_FILE, 'rb') as input:
        encodedFaces = pickle.load(input)
        print("faces in model : {} ".format(encodedFaces.keys()))


def remove_from_model(name, filename):
    if os.path.isfile(filename):
        with open(filename, 'rb') as input:
            encodedFaces = pickle.load(input)
        del encodedFaces[name]
        with open(filename, 'wb') as output:
            pickle.dump(encodedFaces, output, pickle.HIGHEST_PROTOCOL)
            print("Face %s removed from model %s " % (name, MODEL_FILE))


def save_to_model(name, encoded_img, filename):
    if os.path.isfile(filename) :
        print("append model with %s" % name)
        with open(filename, 'rb') as input:
            encodedFaces = pickle.load(input)

        encodedFaces[name] = encoded_img

        with open(filename, 'wb') as output:
            pickle.dump(encodedFaces, output, pickle.HIGHEST_PROTOCOL)
            print("Face %s saved to model %s " % (name, MODEL_FILE))


    else:
        print("Create model with %s" % name)
        with open(filename, 'wb') as output:
            encodedFaces = {name: encoded_img}
            pickle.dump(encodedFaces, output, pickle.HIGHEST_PROTOCOL)


def encode_face(image):
    basename = os.path.splitext(os.path.basename(image))[0]
    img = face_recognition.load_image_file(image)
    encodings = face_recognition.face_encodings(img)

    if len(encodings) > 1:
        click.echo("WARNING: More than one face found in {}. Only considering the first face.".format(file))
        return "", None

    if len(encodings) == 0:
        click.echo("WARNING: No faces found in {}. Ignoring file.".format(file))
        return "", None
    else:
        return basename, encodings[0]



@click.group()
def cli():
    pass

@cli.command('show')
@click.option('--model', default=MODEL_FILE, help='Specify a model (default is ' + MODEL_FILE + ')')
def show(model):
    """Display the face names saved in model"""
    model = model if model != "" else MODEL_FILE
    show_model(model)


@cli.command('remove')
@click.option('--model', default=MODEL_FILE, help='Specify a model (default is ' + MODEL_FILE + ')')
@click.argument('face_to_remove')
def remove(model, face_to_remove):
    """Remove the given face name from the model"""

    model = model if model != "" else MODEL_FILE
    remove_from_model(face_to_remove, model)
    show_model(model)

@cli.command('add')
@click.option('--model', default=MODEL_FILE, help='Specify a model (default is ' + MODEL_FILE + ')')
@click.argument('image_path')
def add(model, image_path):
    """Add to the model the face found in the given image"""

    model = model if model != "" else MODEL_FILE
    name, encoded_img = encode_face(image_path)
    if name != "":
        save_to_model(name, encoded_img, model)
        show_model(model)
    else:
        click.echo('Error')

if __name__ == "__main__":
    cli()
