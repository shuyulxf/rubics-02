# Context

This is a simple Python Flask calendar app for extracting deadlines from users' natural language. In its current state, the app is only intended to support future single-day deadlines. Parsing of past dates is currently out of scope. 

The app assumes that structured dates are written in "**YYYY-MM-DD**", "**DD-MM-YYYY**", or "**DD-MM**" formats (e.g., not "MM-DD-YYYY").

The app allows for the use of the "@" symbol in place of the word "at" (e.g., "Meeting @ 3:00 PM").

The app is primarily intended to support (i.e., has unit tests for) the following date and time formats:

## Dates
- "**YYYY-MM-DD**"
- "**YYYY/MM/DD**"
- "**DD-MM-YYYY**"
- "**DD/MM/YYYY**"
- "**DD-MM**"
- "**DD/MM**"
- "**\[first/second/third/fourth/fifth/last/1st/2nd/3rd/4th/5th] \[weekday] of next month**"
- "**\[first/second/third/fourth/.../thirty-first/1st/2nd/3rd/4th/.../31st] of \[month] \[year]**"
- "**\[first/second/third/fourth/.../thirty-first/1st/2nd/3rd/4th/.../31st] of \[month]**"

## Times
- "**hh:mm**" (assumes 24-hour clock)
- "**hh:mm AM/PM**" (assumes 12-hour clock)

# Docker Dev Env for Python Flask

Docker configuration is based on Raven's [GitHub template for a dockerized Python Flask application](https://github.com/aidt001/docker-python-pip-flask).

# Running tests

This command builds a docker image with the code of this repository and runs the repository's tests.

Windows:
```sh
./build_docker.sh my_app
docker run -t my_app sh ./run_tests.sh
```

Linux/Unix:
```sh
./build_docker.sh my_app
docker run -t my_app ./run_tests.sh
```

Example output:
```
[+] Building 0.1s (10/10) FINISHED                                                            docker:default
 => [internal] load build definition from Dockerfile                                                    0.0s
 => => transferring dockerfile: 248B                                                                    0.0s
 => [internal] load metadata for docker.io/library/python:3.13.2-alpine3.21@sha256:323a717dc4a010fee21  0.0s
 => [internal] load .dockerignore                                                                       0.0s
 => => transferring context: 94B                                                                        0.0s
 => [1/5] FROM docker.io/library/python:3.13.2-alpine3.21@sha256:323a717dc4a010fee21e3f1aac738ee10bb48  0.0s
 => [internal] load build context                                                                       0.0s
 => => transferring context: 253B                                                                       0.0s
 => CACHED [2/5] WORKDIR /app                                                                           0.0s
 => CACHED [3/5] COPY requirements.txt .                                                                0.0s
 => CACHED [4/5] RUN pip install --no-cache-dir -r requirements.txt                                     0.0s
 => CACHED [5/5] COPY . .                                                                               0.0s
 => exporting to image                                                                                  0.0s
 => => exporting layers                                                                                 0.0s
 => => writing image sha256:4e6c980fbf83b2131359af3d3730e61c89ae7dc85e23c151114b0d9d4a749158            0.0s
 => => naming to docker.io/library/my_app                                                               0.0s

....
----------------------------------------------------------------------
Ran 4 tests in 0.069s

OK
```

# Running a flask dev server

Run this command to enable hot reloading via docker.

Windows:
```sh
./build_docker.sh my_app
docker run -v "$(pwd -W):/app" -e FLASK_APP=app -t my_app python3 -m flask init_db
docker run -p 5000:5000 -v "$(pwd -W)":/app -t my_app python3 -m flask run --host=0.0.0.0
```

Linux/Unix:
```sh
./build_docker.sh my_app
docker run --network=host -v .:/app -t my_app flask init_db
docker run --network=host -v .:/app -t my_app flask run
```
