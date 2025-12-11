# HFLAV library contribution

## Running the code

To run this project you firstly must create a virtual environment and install all the dependencies inside:

1. `python -m venv .venv`
2. `source .venv/bin/activate`

To install all the dev dependencies (including tests):
- `pip install -e ".[dev]"`

## Runninig the tests

To launch all the tests:

- `pytest tests`

To launch a specific test:

- `pytest tests/test.py`

And to check the coverage:

- `pytest --cov=hflav_zenodo.module`

Where module is a specific module.

e.g: `pytest --cov=hflav_zenodo.source`

## Configuring code analysis locally

You will need:
- docker
- The SonarQube plugin

If you want to analyze the quality of that you are doing, firstly you should launch the docker-compose:

`docker compose up`

If is the first time you do this, you must go to `http://localhost:9000/`, configure your credentials and create a local project (e.g. hflav-project).

After this you should configure the connection with this info:

- Server URL: `http://localhost:9000` (after this click on generate token and click in confirm)
- Connection name: `sonar-hflav-connection`

If you want to check the coverage, you must run these commands:

- `coverage run -m pytest`
- `coverage xml`


Once this config is done, you only need to link the created project with this command (It can be easily generated when you are creating the project and you indicate that it will be local with Python):

- `pysonar --sonar-host-url=http://localhost:9000 --sonar-token=<TOKEN> --sonar-project-key=<PROJECT_KEY>`

Finally, you can now go to the project and see the issues. If you want to correct it, you must go to the file and the sonarqube tab will show the issue.