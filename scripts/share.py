# -*- coding: utf-8 -*-
import subprocess
import os
import re
import json


# TODO: a newly _reco file won't be uploaded in the cozy sharer, because of the stack
# So we need to remove it first (or remove the whole folder ?)
# cozy-stack files exec 'rm -f /<photo-name>/<photo-name>_reco.jpg'


def image_files_in_folder(folder):
    return [os.path.join(folder, f) for f in os.listdir(folder) if re.match(r'.*\.(jpg|jpeg|png)', f, flags=re.I)]

# The photo is uploaded only if at least one face has been found, ie there
# is an entry in the *.name file, unknown or not
def upload_and_share(photo_base_name, files_path, instance, remote_server):
    json_file_path = os.path.join(files_path, photo_base_name + ".json")

    try:
        f = open(json_file_path, 'r')
        data = json.load(f)

        # Upload photo only if at least a face is found
        subjects = data['subjects']
        if len(subjects) > 0:
            docid = upload_photos(photo_base_name, files_path, instance, remote_server)

            for name in data['subjects']:
                if name != "unknown" and name != "":
                    recipient = recipient_instance(name, remote_server)
                    share(files_path, instance, recipient, remote_server)


    except:
        print("No JSON file found: no face on this one")



def upload_photos(photo_base_name, files_path, instance, remote_server):

    images = image_files_in_folder(files_path)
    json_path = os.path.join(files_path, photo_base_name + '.json')
    for img in images:
        if "_reco" in img:
            reco_path = os.path.join(files_path, os.path.basename(img))
            # Force the upload of the reco face
            remote_file_copy(photo_base_name, reco_path, instance, remote_server)
            # Force the upload of the json file
            remote_file_copy(photo_base_name, json_path, instance, remote_server)

    # Create directory in instance
    create_dir(photo_base_name, instance, remote_server)
    if remote_server != "":
        print("copy files on remote from %s" % files_path)
        copy_files_on_remote(files_path, "reco/", remote_server)

    args = "cozy-stack files import --domain " + instance + " --from " + files_path + " --to /" + photo_base_name

    if remote_server != "":
        args = run_command_on_remote(args, remote_server)

    try:
        out = subprocess.Popen(args, stdout=subprocess.PIPE, shell=True).stdout.read()
        print(out)
    except:
        print("Ops error.. continue anyway: the dir might already exists")


# Copy and upload the contacts faces on the sharer instance, for ACL visualization
def remote_face_copy(photo_face_path, instance, remote_server):
    photo_face_basename = os.path.basename(photo_face_path)
    face_name, ext = os.path.splitext(photo_face_basename)

    print("photo name : %s") % face_name
    # Create face dir in cozy if not exists
    create_dir("faces/", instance, remote_server)
    # Create face name dir in cozy
    create_dir("faces/" + face_name, instance, remote_server)
    # Create face name dir in server to upload it
    args = "mkdir faces/" + face_name
    if remote_server != "":
        args = run_command_on_remote(args, remote_server)
        subprocess.Popen(args, stdout=subprocess.PIPE, shell=True).stdout.read()

    if remote_server != "":
        target_dir = "faces/" + face_name + "/"
        copy_target =  target_dir + face_name + "_face" + ext
        copy_files_on_remote(photo_face_path, copy_target, remote_server)

    print("go run import")
    args = "cozy-stack files import --domain " + instance + " --from " + target_dir + " --to /faces/" + face_name


    if remote_server != "":
        args = run_command_on_remote(args, remote_server)
        print("args : %s" % args)

        subprocess.Popen(args, stdout=subprocess.PIPE, shell=True).stdout.read()



# Force the copy of the reco picture or json file, in case it is updated
def remote_file_copy(photo_base_name, photo_reco_path, instance, remote_server):
    #args = "cozy-stack files exec 'rm -r /" + photo_basename + "' --domain " + instance
    # scp reco/IMG_20180322_151248/IMG_20180322_151248_reco.jpg root@demo.cozy.run:/var/lib/cozy/test3.demo.cozy.run/IMG_20180322_151248
    args = "scp " + photo_reco_path + " " + remote_server + ":/var/lib/cozy/" + instance + "/" + photo_base_name + "/"
    print("args remote copy : %s" % args)
    out = subprocess.Popen(args, stdout=subprocess.PIPE, shell=True).stdout.read()
    print(out)


def create_dir(photo_basename, instance, remote_server):
    args = "cozy-stack files exec 'mkdir /" + photo_basename + "' --domain " + instance

    if remote_server != "":
        args = run_command_on_remote(args, remote_server)

    out = subprocess.Popen(args, stdout=subprocess.PIPE, shell=True).stdout.read()
    print(out)


def file_id(photo_basename, instance, remote_server):
    filename, ext = os.path.splitext(photo_basename)
    args = "cozy-stack files exec 'attrs /" + filename + "/" + photo_basename + "' --domain " + instance

    if remote_server != "":
        args = run_command_on_remote(args, remote_server)

    out = subprocess.Popen(args, stdout=subprocess.PIPE, shell=True).stdout.read()
    res = json.loads(out)

    docid = res["id"]
    return docid


# Returns the recipient cozy instance based on the name and create it if needed 
def recipient_instance(name, remote_server):
    args = "cozy-stack instances ls"
    if remote_server != "":
        args = run_command_on_remote(args, remote_server)

    out = subprocess.Popen(args, stdout=subprocess.PIPE, shell=True).stdout.read()

    instance_name = name.replace(" ?", "")

    if remote_server == "":
        instance_name = instance_name + ".local:8080"
    else:
        instance_name = remote_instance(name, remote_server)

    instance_found = False
    for line in out.splitlines():
        if instance_name in line:
            instance_found = True



    # Create the instance, based on the name
    if not instance_found:
        print("create instance %s" % instance_name)
        if remote_server != "":
            args = "cozy-coclyco create " + instance_name + " paul@cozycloud.cc"
            args = run_command_on_remote(args, remote_server)
        else:
            args = "cozy-stack instances add --dev --email paul@cozycloud.cc " + \
                    "--public-name " + name + " --passphrase cozy --apps " + \
                    "drive,photos,settings " + instance_name
        try:
            out = subprocess.Popen(args, stdout=subprocess.PIPE, shell=True).stdout.read()
            if remote_server == "":
                add_entry_hosts(instance_name)

        except:
            print("ops error... continue anyway")

    return instance_name



def add_entry_hosts(instance_name):
    i = instance_name.split(":")[0]
    print("instance : %s" % i)
    with open('/etc/hosts', 'a') as f:
        f.write('127.0.0.1 ' + i + '\n')
        f.write('127.0.0.1 drive.' + i + '\n')
        f.write('127.0.0.1 photos.' + i + '\n')
        f.write('127.0.0.1 settings.' + i + '\n')


def share(files_path, instance, recipient_instance, remote_server):
    images = image_files_in_folder(files_path)
    for img in images:
        if "_reco" not in img:
            print("share %s from %s with %s " % (img, instance, recipient_instance))

            # Get file id in cozy
            docid = file_id(os.path.basename(img), instance, remote_server)
            print("get file id : %s" % docid)

            # share it!
            if remote_server == "":
                sharing_script_path = os.path.join(os.path.dirname(__file__), "full_sharing.sh")
                args = sharing_script_path + " " + docid + " true " + instance + " " + recipient_instance
            else:
                sharing_script_path = os.path.join(os.path.dirname(__file__), "full_sharing_remote.sh")
                args = sharing_script_path + " " + docid + " true " + instance + " " + recipient_instance + " " + remote_server

            print("run %s" % args)
            out = subprocess.call(args, shell=True)
            #out = subprocess.Popen(args, stdout=subprocess.PIPE).stdout.read()
            print(out)

def run_command_on_remote(command, remote_server):
    # use the 'r' flag for raw string : don't interpret the '\'' for ssh
    command = command.replace("'", r"'\''" )
    command = "ssh " + remote_server + " '" + command + "'"
    return command

def copy_files_on_remote(file_path, target, remote_server):
    args = "scp -r " + file_path + " " + remote_server + ":" + target
    print("run %s" % args)
    res = subprocess.check_output(args.split())
    print(res)

def remote_instance(name, remote_server):
    server_host = remote_server.split('@')[1]
    return name + "." + server_host
