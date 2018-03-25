# -*- coding: utf-8 -*-
from PIL import Image, ImageFont, ImageDraw
import click
import face_recognition
import warnings
import re
import os
import sys
import pickle
import codecs
import sys
import json

reload(sys)
sys.setdefaultencoding('utf8')

MODEL_FILE = "models/model.pkl"

def image_files_in_folder(folder):
    return [os.path.join(folder, f) for f in os.listdir(folder) if re.match(r'.*\.(jpg|jpeg|png)', f, flags=re.I)]

def replace_non_ascii_characters(str):
    str = str.replace('ç', 'c')
    str = str.replace('é', 'e')
    str = str.replace('è', 'e')
    str = str.replace('à', 'a')
    str = str.replace('ù', 'u')
    return str

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
def drawRectangleAroundFaces(image, image_path, output_path, face_locations, face_names, distances, show_distance):
    # Let's trace out each facial feature in the image with a line!
    pil_image = Image.fromarray(image)
    d = ImageDraw.Draw(pil_image)

    for face_location, face_name, distance in zip(face_locations, face_names, distances):

        top, right, bottom, left = face_location
        #print("A face is located at pixel location Top: {}, Left: {}, Bottom: {}, Right: {}".format(top, left, bottom, right))

        # Be careful with coordinates orders, eg left for x, top for y
        # A simpler rectangle method exist, but the width cannot be specified...
        d.line([(left, top), (right, top)], fill=(0, 204, 0), width=5)
        d.line([(right, top), (right, bottom)], fill=(0, 204, 0), width=5)
        d.line([(right, bottom), (left, bottom)], fill=(0, 204, 0), width=5)
        d.line([(left, bottom), (left, top)], fill=(0, 204, 0), width=5)

        xTextName = (right + left) / 2
        yTextName = bottom + 15
        fontsize = 100
        font = ImageFont.truetype("arialbd.ttf", fontsize)
        d.text([xTextName, yTextName], text=face_name, fill=(0,180,0), font=font)

        if show_distance:
            xTextDist = xTextName
            yTextName = yTextName + fontsize + 10
            font = ImageFont.truetype("arialbd.ttf", fontsize / 2)
            d.text([xTextName, yTextName], text=str("%.2f" % distance), fill=(0,180,0), font=font)


    # pil_image.show()

    # Save file


    baseName = os.path.splitext(os.path.basename(image_path))[0]
    extension = os.path.splitext(image_path)[1]
    newRecoFile = baseName + "_reco" + extension
    # this might be only useful for demo: only the reco file is relevant outside demo, so no dedicated dir is needed
    output_path = os.path.join(output_path, baseName)

    newRecoFile = os.path.join(output_path, newRecoFile)
    print("Save file to : %s" % newRecoFile)
    pil_image.save(newRecoFile)

    # TODO: THIS IS ONLY FOR DEMO
    metadataFile = baseName + ".json"
    metadataFile = os.path.join(output_path, metadataFile)

    for i, name in enumerate(face_names):
        name = replace_non_ascii_characters(name)
        if " ?" in name:
            face_names[i] = name.replace(" ?", "")

    data = {
        "class": "acl",
        "doc": newRecoFile,
        "subjects": face_names
    }

    with open(metadataFile, 'w') as outfile:
        json.dump(data, outfile)

    # file = codecs.open(metadataFile,"w", encoding="utf-8")
    # for name in face_names:
    #     name = replace_non_ascii_characters(name)
    #     if " ?" in name:
    #         name = name.replace(" ?", "")
    #     file.write(name + '\n')
    # file.close()
    print("Save metadata to : %s" % metadataFile)


def recognize(image_path, model, tolerance, output_path, show_distance):
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

    if len(face_locations) > 0:

        # Compare model faces with all the detected faces in the image
        face_names = []
        face_distances = []
        for face_encoding in face_encodings:

            # Compute the distances between the face and all the model's faces
            distances = face_recognition.face_distance(model_encoded_images, face_encoding)

            # Keep the distances below the tolerance threshold
            names = []
            dists = []
            for i, dist in enumerate(distances):
                if dist <= tolerance:
                    names.append(model_face_names[i])
                    dists.append(dist)

            # One face has matched: keep it
            if len(names) is 1:
                face_names.append(names[0])
                face_distances.append(dists[0])
                print("%s spotted!" % names[0])
            # Several faces have matched: keep the closest
            elif len(names) > 1:
                print("more than one face match this one")
                print("distances : %s" % dists)
                idx = dists.index(min(dists))
                face_names.append(names[idx] + " ?")
                face_distances.append(dists[idx])

            # None face has matched
            else:
                face_names.append("unknown")
                face_distances.append(-1)
                print("unknown face :/ ")

        # Draw faces rectangle on image
        drawRectangleAroundFaces(
            input_image,
            image_path,
            output_path,
            face_locations,
            face_names,
            face_distances,
            show_distance)



@click.command()
@click.argument('image_path')
@click.option('--model', default=MODEL_FILE, help='Face model to use')
@click.option('--tolerance', default=0.53, help='Minimal distance to match a face. The lower the stricter')
@click.option('--output_path', default='.', help='Path to save the recognized files')
@click.option('--show-distance', default=False, help='Display the distance for each recognized face')
def main(image_path, model, tolerance, output_path, show_distance):
    # Separate in another function to allowed the call from other script
    recognize(image_path, model, tolerance, output_path, show_distance)


if __name__ == "__main__":
    main()
