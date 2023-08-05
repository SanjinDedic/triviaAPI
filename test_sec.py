import os
import sys
from fastapi import Depends
from fastapi_jwt_auth import AuthJWT
from fastapi.testclient import TestClient
import subprocess
import pytest

# Append the parent directory of the root folder to the system path
#sys.path.append(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
# Set the working directory to the root folder
#os.chdir(os.path.dirname(os.path.realpath(__file__)))

os.environ["TESTING"] = "True"
from main import app


client = TestClient(app)


def setup_module(module):
    os.environ["TESTING"] = "True"
    script_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'reset_comp_db.py')
    subprocess.run(['python3', script_path])

def teardown_module(module):
    os.environ["TESTING"] = "False"


def test_read_main():
    response = client.get("/test")
    assert response.status_code == 200
    assert response.json() == {"message":"This is a test"}


def test_quick_signup_sec():
    response = client.post("/quick_signup_sec", 
                           json={"name": "Booya"})
    assert response.status_code == 200
    assert "access_token" in response.json()


def signup_sec():
    response = client.post("/quick_signup_sec", 
                           json={"name": "Booya"})
    print(response.status_code)
    print(response.text)


def test_get_comp_table():
    response = client.get("/get_comp_table")
    assert response.status_code == 200
    assert response.json() is not None


def test_submit_answer_sec():
    response = client.post("/submit_answer_sec", 
                           json={"id": "1", 
                                 "answer": "d",
                                 "team_name": "GitTest"})
    assert response.status_code == 200
    assert response.json()["message"] == "Correct"


def test_submit_incorrect_answer_sec():
    response = client.post("/submit_answer_sec", 
                           json={"id": "2", 
                                 "answer": "d",
                                 "team_name": "GitTest"})
    assert response.status_code == 200
    assert response.json()["message"] == "Incorrect"



def test_submit_ans_violate():
    response = client.post("/submit_answer_sec", 
                           json={"id": "2", 
                                 "answer": "Zero-day vulnerabilities",
                                 "team_name": "GitTest"})
    assert response.status_code == 200
    assert 'question already attempted' in response.json()["security error"]





def submit_answer_sec():
    response = client.post("/submit_answer_sec", 
                           json={"id": "1", 
                                 "answer": "d",
                                 "team_name": "GitTest"})
    print(response.status_code)
    print(response.text)

if __name__ == "__main__":
    submit_answer_sec()
    print("test done -----------------------")
    submit_answer_sec()
    print("test done -----------------------")
    submit_answer_sec()
    signup_sec()