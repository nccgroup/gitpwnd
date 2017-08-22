from flask import Flask
from gitpwnd.util.file_helper import FileHelper
from flask_basicauth import BasicAuth
import yaml
import os
import ipdb

app = Flask(__name__)

# Parse basic auth creds from file
with open("server_creds.yml", 'r') as f:
    server_config = yaml.load(f)

app.config['BASIC_AUTH_USERNAME'] = server_config["basic_auth_username"]
app.config['BASIC_AUTH_PASSWORD'] = server_config["basic_auth_password"]
app.config['HOOK_SECRET'] = server_config["hook_secret"]

# TODO: fix the naming confusion. This is the path to a local version of the repo
# we're using for command and control
app.config["BACKDOORED_REPOS_PATH"] = os.path.dirname(server_config["benign_repo_path"])

app.config["APP_ROOT"] = os.path.dirname(os.path.abspath(__file__))

app.config["INTEL_ROOT"] = os.path.join(app.config["BACKDOORED_REPOS_PATH"], "..", "intel")
app.config["INTEL_ROOT"] = os.path.abspath(app.config["INTEL_ROOT"])

basic_auth = BasicAuth(app)

# Ensure some directories we'll be storing important things in are created
FileHelper.ensure_directory(app.config["BACKDOORED_REPOS_PATH"])
FileHelper.ensure_directory(app.config["INTEL_ROOT"])

from gitpwnd import controllers
