# -*- coding: utf-8 -*-

import face_recognition
import picamera
import click
import pickle
import numpy as np

# This is a demo of running face recognition on a Raspberry Pi.
# This program will print out the names of anyone it recognizes to the console.

# To run this, you need a Raspberry Pi 2 (or greater) with face_recognition and
# the picamera[array] module installed.
# You can follow this installation instructions to get your RPi set up:
# https://gist.github.com/ageitgey/1ac8dbe8572f3f533df6269dab35df65
# Get a reference to webcam #0 (the default one)

# Get a reference to the Raspberry Pi camera.
# If this fails, make sure you have a camera connected to the RPi and that you
# enabled your camera in raspi-config and rebooted first.
camera = picamera.PiCamera()
camera.resolution = (320, 240)
output = np.empty((240, 320, 3), dtype=np.uint8)

# Initialize some variables
face_locations = []
face_encodings = []
face_names = []

MODEL_FILE = "model.pkl"

@click.command()
@click.option('--model', default=MODEL_FILE, help='Face model to use')
def main(model):
    # Extract known faces from model
    model_encoded_images = []
    model_face_names = []
    print("open model %s" % model   )
    with open(model, 'rb') as input:
        encodedFaces = pickle.load(input)
        print("faces found in model : %s " % encodedFaces.keys())

        for k, v in encodedFaces.iteritems():
            model_face_names.append(k)
            model_encoded_images.append(v)


    process_this_frame = True

    while True:
        # Grab a single frame of video from the RPi camera as a numpy array
        camera.capture(output, format="rgb")

        # Resize frame of video to 1/4 size for faster face recognition processing
        small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)

        # Only process every other frame of video to save time
        if process_this_frame:
            # Find all the faces and face encodings in the current frame of video
            face_locations = face_recognition.face_locations(output)
            face_encodings = face_recognition.face_encodings(output, face_locations)

            face_names = []
            for face_encoding in face_encodings:
                # See if the face is a match for the known face(s)
                matches = face_recognition.compare_faces(model_encoded_images, face_encoding, 0.55)
                faceFound = False
                for i, res in enumerate(matches):
                    if res:
                        print("%s match!" % model_face_names[i])
                        face_names.append(model_face_names[i])
                        faceFound = True
                        break
                if not faceFound:
                    face_names.append("Unknown")

        process_this_frame = not process_this_frame


if __name__ == "__main__":
    main()
