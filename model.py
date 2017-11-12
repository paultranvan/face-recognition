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
    with open(model, 'rb') as input:
        encodedFaces = pickle.load(input)
        print("faces in model {}: {} ".format(model, encodedFaces.keys()))


def remove_from_model(name, filename):
    if os.path.isfile(filename):
        with open(filename, 'rb') as input:
            encodedFaces = pickle.load(input)
        del encodedFaces[name]
        with open(filename, 'wb') as output:
            pickle.dump(encodedFaces, output, pickle.HIGHEST_PROTOCOL)
            print("Face %s removed from model %s " % (name, MODEL_FILE))


def save_to_model(name, encoded_img, model_filename):
    if os.path.isfile(model_filename) :
        with open(model_filename, 'rb') as input:
            encodedFaces = pickle.load(input)

        if name in encodedFaces:
            print("WARNING: " + name + " already exists in this model")
            return

        encodedFaces[name] = encoded_img

        with open(model_filename, 'wb') as output:
            pickle.dump(encodedFaces, output, pickle.HIGHEST_PROTOCOL)
            print("Face %s saved to %s " % (name, MODEL_FILE))


    else:
        print("Create model with %s" % name)
        with open(model_filename, 'wb') as output:
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


def list_images(path):
    # List only the files in the directory
    images = list()
    for dir_, _, files in os.walk(path):
        for fileName in files:
            relDir = os.path.relpath(dir_, '.')
            relFile = os.path.join(relDir, fileName)
            images.append(relFile)
    return images


def add_face(image_path, model):
    name, encoded_img = encode_face(image_path)
    if name != "":
        save_to_model(name, encoded_img, model)
    else:
        print("Error with %s" % image_path)


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
@click.option('--directory', default=False, help='Add all the faces in the directory', type=bool)
@click.argument('image_path')
def add(model, directory, image_path):
    """Add to the model the face found in the given image"""

    model = model if model != "" else MODEL_FILE

    if directory:
        images = list_images(image_path)
        print("files in directory : {} ".format(images))
        for img in images:
            print("image : %s" % img)
            add_face(img, model)

    else:
        add_face(image_path, model)

if __name__ == "__main__":
    cli()
