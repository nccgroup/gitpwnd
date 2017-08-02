# GitPwnd Server

The GitPwnd server listens for webhook pushes from GitHub (currently) or other
git providers that occur when a `git push` has occurred to the command and
control git repo set up by `../setup.py`.

It then automatically extracts the output of the commands run by the
compromised machine and stores them locally.

The web interface then allows you to view the extracted information.

## Getting Set Up

~~~
$ pip install -r requirements.txt --user

# or use virtualenv, etc
~~~

## Running

~~~
$ python3 server.py
~~~

## Routes

Quick notes on important routes:

* POST `/api/repo_push` - hook you set up in GitLab/GitHub/etc for the backdoored repo that sends a push whenever the repo is pushed to.
  * [GitHub docs](https://developer.github.com/webhooks/)
  * [Gitlab docs](https://gitlab.com/gitlab-org/gitlab-ce/blob/master/doc/user/project/integrations/webhooks.md) - will integrate in the future.

