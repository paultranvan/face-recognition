request = require('request')
fs = require('fs')
async = require('async')

config = require('./import_contacts.json');

COZY_URL = config.url
SAVE_DIR = config.save_dir
RUN_INTERVAL = config.run_interval

setInterval(function() {
    console.log("Let's check contacts");

    logIn(function(err) {
        if (err) {
            console.error(err)
        } else {
            getContacts(function(err) {
                if(err) {
                    console.error(err)
                }
            })
        }
    })
}, RUN_INTERVAL)

logIn(function(err) {
    if (err) {
        console.error(err)
    } else {
        getContacts(function(err) {
            if(err) {
                console.error(err)
            }
        })
    }
})

function logIn(callback) {
    options = {
        url: COZY_URL + "/login",
        method: 'POST',
        jar: true,
        json: true,
        body: {
            password: config.password,
            authcode: ''
        }
    }
    request(options, function(err, res, body) {
        if(err) {
            callback(err)
        } else if(res.statusCode > 300) {
            err = "Error : code " + res.statusCode
            callback(err)
        } else {
            console.log('login successufl')
            callback()
        }
    })
}

function getContacts(callback) {
    options = {
        url: COZY_URL + "/apps/contacts/contacts",
        jar: true,
        json: true
    }
    request(options, function(err, res, contacts) {
        if(err) {
            callback(err)
        } else if(res.statusCode > 300) {
            err = "Error : code " + res.statusCode
            callback(err)
        } else {
            async.eachSeries(contacts, function(contact, next) {
                if(contact._attachments) {
                    getPhoto(contact, function(err) {
                        next(err)
                    })
                } else {
                    next()
                }
            }, function(err) {
                callback(err)
            })
        }
    })
}

function getPhoto(contact, callback) {
    url = COZY_URL + "/apps/contacts/contacts/" + contact.id + "/picture.png?revpos=2"
    options = {
        url: url,
        jar: true,
        json: true
    }
    fullName = contact.fn.replace(" ", "_")
    fileName = SAVE_DIR + fullName + ".jpg"
    fs.stat(fileName, function(err, stats) {
        if(err) {
            stream = request(options, function(err, res, photo) {
                if(err) {
                    callback(err)
                } else if(res.statusCode > 300) {
                    err = "Error : code " + res.statusCode
                    callback(err)
                }
            })
            stream.pipe(fs.createWriteStream(fileName))
            console.log(fileName + ' created')
            stream.end()
            callback()
        } else {
            callback()
        }
    })
}
