# -*- coding: utf-8 -*-
from PIL import Image, ImageFont, ImageDraw
import click
import face_recognition
import warnings
import re
import click
import os
import pickle

MODEL_FILE = "model.pkl"

def image_files_in_folder(folder):
    return [os.path.join(folder, f) for f in os.listdir(folder) if re.match(r'.*\.(jpg|jpeg|png)', f, flags=re.I)]


# Adapt the font size depending on the image size
def computeFontSize(image_path, text):
    # We have to load again, because we used the face_reco api, which doesn't
    # return an Image object
    image = Image.open(image_path)

    fontsize = 1
    # the text must be greater than this image fraction
    img_fraction = 0.1

    font = ImageFont.truetype("arial.ttf", fontsize)
    while font.getsize(text)[0] < img_fraction*image.size[0]:
        fontsize += 1
        font = ImageFont.truetype("arial.ttf", fontsize)

    # optionally de-increment to be sure it is less than criteria
    fontsize -= 1
    return fontsize


# Scan the faces directory to extract the names and faces encodings
def scan_known_people(folder):
    known_names = []
    known_face_encodings = []

    for file in image_files_in_folder(folder):
        basename = os.path.splitext(os.path.basename(file))[0]
        img = face_recognition.load_image_file(file)
        encodings = face_recognition.face_encodings(img)

        if len(encodings) > 1:
            click.echo("WARNING: More than one face found in {}. Only considering the first face.".format(file))

        if len(encodings) == 0:
            click.echo("WARNING: No faces found in {}. Ignoring file.".format(file))
        else:
            known_names.append(basename)
            known_face_encodings.append(encodings[0])

    return known_names, known_face_encodings


# Draw a green rectangle for each spotted face
def drawRectangleAroundFaces(image, image_path, face_locations, face_names):
    # Let's trace out each facial feature in the image with a line!
    pil_image = Image.fromarray(image)
    d = ImageDraw.Draw(pil_image)

    for face_location, face_name in zip(face_locations, face_names):

        top, right, bottom, left = face_location
        print("A face is located at pixel location Top: {}, Left: {}, Bottom: {}, Right: {}".format(top, left, bottom, right))

        # Be careful with coordinates orders, eg left for x, top for y
        # A simpler rectangle method exist, but the width cannot be specified...
        d.line([(left, top), (right, top)], fill=(0, 204, 0), width=5)
        d.line([(right, top), (right, bottom)], fill=(0, 204, 0), width=5)
        d.line([(right, bottom), (left, bottom)], fill=(0, 204, 0), width=5)
        d.line([(left, bottom), (left, top)], fill=(0, 204, 0), width=5)

        xText = (right + left) / 2
        yText = bottom + 35
        fontsize = computeFontSize(image_path, face_name)
        font = ImageFont.truetype("arial.ttf", fontsize)
        d.text([xText, yText], text=face_name, fill=(0,204,0), font=font)

    pil_image.show()

    # Save file
    baseName = os.path.splitext(image_path)[0]
    extension = os.path.splitext(image_path)[1]
    newFile = baseName + "_reco" + extension
    print("Save file to : %s" % newFile)
    pil_image.save(newFile)

@click.command()
@click.argument('image_path')
@click.option('--model', default=MODEL_FILE, help='Face model to use')
def main(image_path, model):

    # Extract known faces from model
    model_encoded_images = []
    model_face_names = []
    with open(model, 'rb') as input:
        encodedFaces = pickle.load(input)
        print("faces found in model : %s " % encodedFaces.keys())

        for k, v in encodedFaces.iteritems():
            model_face_names.append(k)
            model_encoded_images.append(v)

    #print "Get the known faces..."
    #known_names, known_face_encodings = scan_known_people("faces")

    # Load the jpg file into a numpy array
    input_image = face_recognition.load_image_file(image_path)
    #unknown_face_encoding = face_recognition.face_encodings(unknown_image)[0]
    face_encodings = face_recognition.face_encodings(input_image)
    face_locations = face_recognition.face_locations(input_image)

    print("{} face(s) found in this photograph.".format(len(face_locations)))

    # Compare model faces with all the detected faces in the image
    face_names = []
    for face_encoding in face_encodings:
        results = face_recognition.compare_faces(model_encoded_images, face_encoding, 0.6)
        faceFound = False
        for i, res in enumerate(results):
            if res:
                print("%s match this photo!" % model_face_names[i])
                face_names.append(model_face_names[i])
                faceFound = True
                break
        if not faceFound:
            face_names.append("Unknown")
            print("unknown face :/ ")

    #print("I found {} face(s) in this photograph.".format(len(face_locations)))

    # Draw faces rectangle on image
    drawRectangleAroundFaces(input_image, image_path, face_locations, face_names)

if __name__ == "__main__":
    main()
