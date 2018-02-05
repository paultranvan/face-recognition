# Face recognition

This mainly uses this [API](https://github.com/ageitgey/face_recognition) for the face detection and recognition, which is itself based on [Dlib](http://dlib.net/) with a trained model.

## Concepts

Faces are saved into a local model, used to recognize persons in photos.

There are 2 scripts:
* `model.py`: used to create, visualize or remove from the model.
* `photo_face_reco.py`: used to detect and recognize faces in a given photo, thanks to the built model.

## Usage

For first use, run `python model.py add <path_photo>` to initialize the model with a face. When adding a photo to the model, make sure there is only one face, clearly displayed, e.g. no sunglasses, no profile, etc.
By default, it creates a `model.pkl` file.

Once you have a model with at least one face, you can run `python photo_face_reco.py <path_photo>`. It will try to recognize faces from the given photo thanks to the ones saved in the model. The result is saved in a file `new.jpg`.
