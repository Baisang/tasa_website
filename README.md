# TASA Website

This repo contains the source code for the UC Berkeley [Taiwanese American Student Association](http://tasa.berkeley.edu) website. It is currently hosted by the [Open Computing Facility](https://ocf.io).

## Conventions

1. Don't do `git add .` or `git add -A`, just do `git add -u` to only add changes for tracked files
2. Don't track files that contain sensitive information such as OAuth keys, API keys, or passwords
3. Keep things as simple as possible, no need to have too many fancy features
4. Try not to edit on the live servers, because that is bad
5. Don't drop a bunch of tables in the sqlite db

## Developer Setup
Here is how to set up a local version of the website on your own machine.

1. Clone the repository using git
2. Install [virtualenv](https://virtualenv.pypa.io/en/stable/installation/)
3. `make venv` should create your `venv` for you, if you need to do anything with that.
4. Make a file called `config.yaml` at the same level and similar to the `config.yaml.template` file in `tasa_website/`. Put in an admin account username, password, secret key, and Facebook API token. These will only be active for your local running instance.
5. `make run` to start everything locally. You should be able to view your site locally at `localhost:5000`

