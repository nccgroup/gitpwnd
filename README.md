# GitPwnd

GitPwnd is a tool to aid in network penetration tests. GitPwnd allows an
attacker to send commands to compromised machines and receive the results back
using a git repo as the command and control transport layer. By using git as the
communication mechanism, the compromised machines don't need to communicate
directly with your attack server that is likely at a host or IP that's
untrusted by the compromised machine.

Currently GitPwnd assumes that the command and control git repo is hosted on
GitHub, but this is just an implementation detail for the current iteration.
The same technique is equally applicable to any service that can host a git
repo, whether it is BitBucket, Gitlab, etc.

## Setup and Installation

The GitPwnd setup script (`setup.py`) and server (`server/`) were written and
tested using Python3, but Python 2.7 will likely work as well. The bootstrapping process
to set up persistence on compromised machines was tested on Python 2.7.

### Set up GitPwnd
```
# Install Python dependencies
$ pip3 install -r requirements.txt --user

# Set up config
$ cp config.yml.example config.yml
# Configure config.yml with your custom info

# Run the setup script
$ python3 setup.py config.yml
```

### Run the GitPwnd Server

~~~
$ cd server/
$ pip3 install -r requirements.txt --user
$ python3 server.py
~~~

## Contributing

Contributions welcome! Please feel free to file an issue or PR and we'll get
back to you as soon as possible.

## Version Info

### v0.1

* Initial PoC feature-complete for BlackHat USA 2017.

## TODO

* [ ] Write a much more descriptive README
