import os
import json
import git  # gitpython

from gitpwnd import app
from gitpwnd.util.file_helper import FileHelper

class GitHelper:

    # http://stackoverflow.com/questions/12179271/python-classmethod-and-staticmethod-for-beginner
    @staticmethod
    def save_intel(repo_name, branch_name, repo_path, intel_root):
        # TODO: "results.json" is hardcoded in payload.py
        # this should be abstracted to config.yml or something
        intel_file = os.path.join(repo_path, "results.json")
        print("[*] Reading intel file from: %s" % intel_file)
        with open(intel_file, 'r') as f:
            intel_json = json.load(f)

        # Have subdir for each node's intel
        node_id = branch_name
        output_dir = os.path.join(intel_root, repo_name, node_id)
        FileHelper.ensure_directory(output_dir)
        output_file = os.path.join(output_dir, "%s.json" % intel_json["time_ran"].replace(" ", "_"))
        print("[*] Storing intel file to: %s" % output_file)

        with open(output_file, 'w') as f:
            json.dump(intel_json, f)

    @staticmethod
    def import_intel_from_branch(repo_name, branch_name, backdoored_repos_root, intel_root):

        repo_path = os.path.join(backdoored_repos_root, repo_name)
        repo = git.Repo(repo_path)

        # http://gitpython.readthedocs.io/en/stable/tutorial.html#using-git-directly
        # Tried using the other ways of using gitpython but this appears easiest
        g = repo.git

        g.pull() # make sure we have the latest branches
        g.checkout(branch_name)
        g.pull() # make sure we have the latest results.json

        GitHelper.save_intel(repo_name, branch_name, repo_path, intel_root)

        g.checkout("master")
