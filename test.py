import os
import sys
from fastapi import Depends
from fastapi_jwt_auth import AuthJWT
from fastapi.testclient import TestClient
import pytest
import subprocess

# Append the parent directory of the root folder to the system path
#sys.path.append(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
# Set the working directory to the root folder
#os.chdir(os.path.dirname(os.path.realpath(__file__)))

os.environ["TESTING"] = "True"
from main import app


client = TestClient(app)


def setup_module(module):
    os.environ["TESTING"] = "True"
    script_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'reset_trivia_db.py')
    subprocess.run(['python3', script_path])

def teardown_module(module):
    os.environ["TESTING"] = "False"


def test_read_main():
    response = client.get("/test")
    assert response.status_code == 200
    assert response.json() == {"message":"This is a test"}


def test_quick_signup():
    response = client.post("/quick_signup", 
                           json={"name": "Booya"})
    assert response.status_code == 200
    assert "access_token" in response.json()


def test_get_teams_table():
    response = client.get("/get_teams_table")
    assert response.status_code == 200
    assert response.json() is not None

def test_submit_answer():
    response = client.post("/submit_answer", 
                           json={"id": "1", 
                                 "answer": "a",
                                 "team_name": "Boronia"})
    assert response.status_code == 200
    assert response.json()["message"] == "Correct"

def test_submit_answer2():
    response = client.post("/submit_answer", 
                           json={"id": "1", 
                                 "answer": "b",
                                 "team_name": "Boronia"})
    assert response.status_code == 200
    assert response.json()["message"] == "Incorrect"

def test_submit_wrong_answer():
    response = client.post("/submit_answer", 
                           json={"id": "1", 
                                 "answer": "b",
                                 "team_name": "Wantirna"})
    assert response.status_code == 200
    assert response.json()["message"] == "Incorrect"
