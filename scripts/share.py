# -*- coding: utf-8 -*-
import subprocess
import os
import re
import json


# TODO: to be able to run this in a prod environment, we need to be able to
# know what is the domain name to creat the instance. Also, the local script
# needs to update the /etc/hosts, but not in a prod

# Also, we might have troubles with scheme.


def image_files_in_folder(folder):
    return [os.path.join(folder, f) for f in os.listdir(folder) if re.match(r'.*\.(jpg|jpeg|png)', f, flags=re.I)]

# The photo is uploaded only if at least one face has been found, ie there
# is an entry in the *.name file, unknown or not
def upload_and_share(photo_base_name, files_path, instance):
    names_file_path = os.path.join(files_path, photo_base_name + ".names")

    try:
        file = open(names_file_path, 'r')
    except IOError:
        print("no one found on this photo")
        return
    lines = file.readlines()
    lines = [x.strip() for x in lines]  # Remove blanks characters

    # Upload photo only if at least a face is found
    if len(lines) > 0:
        docid = upload_photos(photo_base_name, files_path, instance)

    for name in lines:
        if "Unknown" not in name and name is not "":
            recipient = recipient_instance(name)
            share(files_path, instance, recipient)


def upload_photos(photo_base_name, files_path, instance):
    images = image_files_in_folder(files_path)

    # Create directory
    create_dir(photo_base_name, instance)

    for img in images:
        if "_reco" not in img:
            args = [
                'cozy-stack',
                'files',
                'import',
                '--domain',
                instance,
                '--from',
                files_path,
                '--to',
                '/' + photo_base_name
            ]
            try:
                res = subprocess.check_output(args)
                for line in res.splitlines():
                    print("%s" % line)

            except:
                print("Ops error.. continue anyway")

def create_dir(photo_basename, instance):
    args = "cozy-stack files exec 'mkdir /" + photo_basename + "' --domain " + instance
    out = subprocess.Popen(args, stdout=subprocess.PIPE, shell=True).stdout.read()
    print(out)


def file_id(photo_basename, instance):
    filename, ext = os.path.splitext(photo_basename)

    args = "cozy-stack files exec 'attrs /" + filename + "/" + photo_basename + "' --domain " + instance
    out = subprocess.Popen(args, stdout=subprocess.PIPE, shell=True).stdout.read()
    res = json.loads(out)

    docid = res["id"]
    return docid

# Returns the recipient cozy instance based on the name and create it if needed 
def recipient_instance(name):
    res = subprocess.check_output(["cozy-stack", "instances", "ls"])
    instance_found = False
    for line in res.splitlines():
        if name in line:
            instance_found = True

    name = name.replace(" ?", "")
    instance_name = name + ".local:8080"

    # Create the instance, based on the name
    if not instance_found:
        print("create instance %s" % instance_name)
        args = [
            'cozy-stack',
            'instances',
            'add',
            '--dev',
            '--email',
            'paul@cozycloud.cc',
            '--public-name',
            name,
            '--passphrase',
            'cozy',
            '--apps',
            'drive,photos,settings',
            instance_name
        ]
        try:
            res = subprocess.check_output(args)
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


def share(files_path, instance, recipient_instance):
    images = image_files_in_folder(files_path)
    for img in images:
        if "_reco" not in img:
            print("share %s from %s with %s " % (img, instance, recipient_instance))

            # Get file id in cozy
            docid = file_id(os.path.basename(img), instance)

            # share it!
            sharing_script_path = os.path.join(os.path.dirname(__file__), "full_sharing.sh")
            args = [
                sharing_script_path,
                docid,
                'true',
                instance,
                recipient_instance
            ]
            res = subprocess.check_output(args)
            #out = subprocess.Popen(args, stdout=subprocess.PIPE).stdout.read()
            print(res)
