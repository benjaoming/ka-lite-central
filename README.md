# KA Lite Central Server

This is the code for the KA Lite Central Server: [https://kalite.learningequality.org](https://kalite.learningequality.org)

The repo contains two branches:

* `develop`: The default branch, deployed to a staging server
* `master`: Intended for deployment, not to be pushed to (except from `develop`)

## What this is

* A Django app which is "It's Complicated" with [ka-lite](https://github.com/learningequality/ka-lite.git).
* Distributed servers (KA Lite) are configured to point to an instance of the central server, which manages their syncing.
* Could be managing many different versions of KA Lite at once.

## Bootstrapping a dev env

1. Install Docker
1. Build assets:

   ```
   make assets
   ```

1. Create a virtualenv and install dependencies

   ```
   mkvirtualenv centralserver
   workon centralserver
   pip install -r requirements.txt
   ```

1. Go into the centralserver directory and bootstrap it:

   ```
   cd centralserver
   python manage.py setup --no-assessment-items
   ```

1. Run the server:

   ```
   cd centralserver
   python manage.py runserver 0.0.0.0:8000
   ```

### Docker workflow

The docker container mounts your current working directory in the container, builds assets and shuts down. All changes are stored directly in your git checkout.

There is no workflow for quickly building assets while editing source files and having a development web server automatically reload. None of that.

If you are changing Docker stuff, remember to run `docker image prune` once in a while to delete garbage images.

### Pointing distributed ka-lite servers to local central server

After cloning the distributed server codebase from https://github.com/learningequality/ka-lite, add the following to its `~/.kalite/settings.py`:

```
CENTRAL_SERVER_HOST   = "127.0.0.1:8000"
SECURESYNC_PROTOCOL   = "http"
```

This will cause it to point to your locally running instance of the central server for registering and syncing.

### Custom local configuration

You may create a `centralserver/local_settings.py` file to customize your setup.

You don't have to. The default is `DEBUG=True` and to use a local sqlite db.

Use `USE_DEBUG_TOOLBAR = True` for the Django debug toolbar.

### Using an online staging database

You will need to install MySQL Python libraries and a local dev library firstly:

```
sudo apt-get install libmysqlclient-dev
pip install -r requirements_production.txt
```

After this, you may add for instance a Google Cloud MySQL instance to `local_settings.py`:

```
DATABASES_KEEP_STAGING = {
    "default": {
        "ENGINE": "django.db.backends.mysql",
        "NAME": "ka_lite_central",
        "USER": "ka_lite_central",
        "PASSWORD": DATABASE_PASSWORD,
        "HOST": "1.2.3.4",
        "PORT": "3306",
        "OPTIONS": {
            "ssl": {
                "ca": "/home/balder/code/ansible-playbooks/roles/keep/files/secrets/staging/server-ca.pem",
                "cert": "/home/balder/code/ansible-playbooks/roles/keep/files/secrets/staging/client-cert.pem",
                "key": "/home/balder/code/ansible-playbooks/roles/keep/files/secrets/staging/client-key.pem",
            }
        },
    }
}

DATABASES = DATABASES_KEEP_STAGING
```
