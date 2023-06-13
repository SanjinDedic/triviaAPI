import os
from fastapi import Depends
from fastapi_jwt_auth import AuthJWT
from fastapi.testclient import TestClient
import pytest
from main import app  # assuming your FastAPI app is named 'app' and is in a file named 'main.py'

client = TestClient(app)


def setup_module(module):
    os.environ["TESTING"] = "True"

def teardown_module(module):
    del os.environ["TESTING"]


def test_read_main():
    response = client.get("/test")
    assert response.status_code == 200
    assert response.json() == {"message":"This is a test"}

def test_get_teams_table():
    response = client.get("/get_teams_table")
    assert response.status_code == 200
    assert response.json() is not None

def test_submit_answer():
    response = client.post("/submit_answer", 
                           json={"id": "1", 
                                 "answer": "a",
                                 "team_name": "Wantirna",
                                 "table": "teams"})
    assert response.status_code == 200
    assert response.json()["message"] == "Correct"
