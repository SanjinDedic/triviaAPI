from fastapi.testclient import TestClient
import pytest
from main import app

client = TestClient(app)


def test_login_failure():
    wrong_team = {
        "team_name": "wrong_team",
        "password": "wrong_password"
    }
    response = client.post("/login", json=wrong_team)
    assert response.status_code == 401
    assert "Invalid team name or password" in response.json()["detail"]




def test_login_and_submit_answer_correct():
    # Log in to get the access token
    login_data = {
        "team_name": "Wantirna",
        "password": "abc"  # Replace with the correct password
    }
    login_response = client.post("/login", json=login_data)
    
    # Check if the login is successful
    assert login_response.status_code == 200
    assert "access_token" in login_response.json()

    access_token = login_response.json()["access_token"]

    # Send the submit_answer request with the correct answer
    submit_answer_data = {
        "id": 1,
        "answer": "a",
        "team_name": "Wantirna",
        "table": "teams"
    }
    headers = {"Authorization": f"Bearer {access_token}"}
    response = client.post("/submit_answer", json=submit_answer_data, headers=headers)

    # Check if the response is correct
    assert response.status_code == 200
    assert response.json() == {"message": "Correct"}

    submit_answer_data = {
        "id": 96,
        "answer": "Tesla",
        "team_name": "Wantirna",
        "table": "teams"
    }
    headers = {"Authorization": f"Bearer {access_token}"}
    response = client.post("/submit_answer", json=submit_answer_data, headers=headers)

    # Check if the response is correct
    assert response.status_code == 200
    assert response.json() == {"message": "Correct"}


def test_test():
    response = client.get("/test")
    assert response.status_code == 200
    assert response.json() == {"message": "This is a test"}

def test_home():
    response = client.get("/")
    assert response.status_code == 200
    assert "length" in response.json()


def test_get_teams_table():
    response = client.get("/get_teams_table")
    assert response.status_code == 200
    assert "teams" in response.json()

def test_signup():
    team = {
        "name": "TestTeam",
        "password": "test123",
        "color": "red"
    }
    response = client.post("/signup", json=team)
    assert response.status_code == 200
    assert response.json() == {"message": "Team created successfully"}

def test_quick_signup():
    team = {
        "name": "QuickTestTeam",
        "color": "blue"
    }
    response = client.post("/quick_signup", json=team)
    assert response.status_code == 200
    assert response.json() == {"message": "Team created successfully"}


def test_save_json():
    data = {
        "quiz_data": [{"name": "TestTeam", "password": "test123", "color": "red"}],
        "filename": "test2"
    }
    response = client.post("/save_json", json=data)
    print(response.json())
    assert response.status_code == 200
    assert response.json() == {"message": "File saved successfully"}



def save_json():
    data = {
        "quiz_data": [{"name": "TestTeam", "password": "test123", "color": "red"}],
        "filename": "test2"
    }
    response = client.post("/save_json", json=data)
    print(response.json())

'''
def test_generate_quiz():
    data = {
        "topic": "football",
        "num": 4
    }
    response = client.post("/generate_quiz", json=data)
    print(response.json())
    assert response.status_code == 200
    assert "id" in response.json()
    assert "type" in response.json()
'''


def generate_quiz():
    data = {
        "topic": "Leeds United",
        "num": 4
    }
    response = client.post("/generate_quiz", json=data)
    print(response.json())