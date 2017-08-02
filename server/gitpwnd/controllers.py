from flask import Flask
from flask import render_template
from flask import redirect
from flask import url_for
from flask import request, session, send_file, send_from_directory
from flask import make_response # for setting cookies
import flask
import ipdb
import json

from functools import wraps

from gitpwnd import app, basic_auth
from gitpwnd.util.git_helper import GitHelper
from gitpwnd.util.file_helper import FileHelper
from gitpwnd.util.intel_helper import IntelHelper

# Basic auth adapted from the following didn't quite do what I wanted
# http://flask.pocoo.org/snippets/8/

# Instead used:
# https://flask-basicauth.readthedocs.io/en/latest/

##########
# Routes #
##########

@app.route("/")
@basic_auth.required
def index():
    return render_template("index.html")

@app.route("/setup")
@basic_auth.required
def setup():
    return render_template("setup.html")

@app.route("/nodes")
@basic_auth.required
def nodes():
    intel_results = IntelHelper.parse_all_intel_files(app.config["INTEL_ROOT"])
    if len(intel_results) == 0:
        return render_template("nodes.html", intel=intel_results)
    else:
        intel_results = IntelHelper.json_prettyprint_intel(intel_results)
        return render_template("nodes.html", intel=intel_results)

##############
# API Routes #
##############

@app.route("/api/repo/receive_branch", methods=["POST"])
def receive_branch():
    repo_name = request.get_json()["repository"]["name"]
    branch = request.get_json()["ref"].split("/")[-1]
    GitHelper.import_intel_from_branch(repo_name, branch, app.config["BACKDOORED_REPOS_PATH"], app.config["INTEL_ROOT"])
    return "OK"
