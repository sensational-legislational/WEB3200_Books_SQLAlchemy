# Directions For Installing Flask-User Basic App

This repo contains installation instructions for Python Version 3.8.2 and 3.10.1 

## Installation for 3.8.2:

- >venv\scripts\activate.bat
- >set flask_app=basic_app.py
- >flask run --port 4000
- In a browser go to localhost:4000

## Installation for 3.10.1:

- >venvTen\scripts\activate.bat
- >set flask_app=basic_app.py
- >flask run --port 4000
- In a browser go to localhost:4000

The codebase contains virtual environments for 3.8 and 3.10 that already have the appropriate libraries and python executables installed.  However, requirements files for both 3.8 and 3.10 have been generated.  This should allow you to create the virtual environments from scratch by typing 

## Installation for 3.8.2:

- >python -m venv venv
- >venv\scripts\activate.bat
- >pip install -r requirements.txt
- >set flask_app=basic_app.py
- >flask run --port 4000

## Installation for 3.10.1, (works with 3.10.6 too):

- >python -m venv venvTen
- >venvTen\scripts\activate.bat
- >pip install -r requirementsTen.txt
- >set flask_app=basic_app.py
- >flask run --port 4000
