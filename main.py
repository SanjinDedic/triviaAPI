import logging
import os
import random
import sqlite3
from datetime import datetime
from difflib import SequenceMatcher

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi_jwt_auth import AuthJWT
from fastapi_jwt_auth.exceptions import AuthJWTException
from pydantic import BaseModel
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import Response
from typing import Optional

# Set up logging
logging.basicConfig(filename='app.log', level=logging.INFO,
                    format='%(asctime)s:%(levelname)s:%(message)s')
logging.info("FastAPI application started")
app = FastAPI()

if os.getenv("TESTING") != "True":
    class CustomCORSMiddleware(BaseHTTPMiddleware):
        async def dispatch(self, request: Request, call_next: RequestResponseEndpoint):
            origin = request.headers.get('origin', None)

            with open("origins.txt", "a") as file:
                file.write(f"Origin: {origin}\n")
            
            allow_origin = False
            if origin:
                if 'aitrivia.live' in origin or '.repl.co' in origin or 'cloudfront.net' in origin or origin.startswith('https://replit.com'):
                    allow_origin = True

            if allow_origin:
                response = await call_next(request)
            else:
                response = Response(content="Access not allowed", status_code=403)

            return response

    app.add_middleware(
        CORSMiddleware,
        allow_origins=['*'],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(CustomCORSMiddleware)


# Database function
def execute_db_query(query, params=(), fetchone=False, db="trivia.db"):
    try:
        conn = sqlite3.connect(db)
        c = conn.cursor()
        c.execute(query, params)
        conn.commit()
        if fetchone:
            return c.fetchone()
        else:
            return c.fetchall()
    except Exception as e:
        logging.error("Error occurred when executing database query", exc_info=True)
        raise e
    finally:
        conn.close()


def similar(s1, s2, threshold=0.6):
    similarity_ratio = SequenceMatcher(None, s1, s2).ratio()
    return similarity_ratio >= threshold

def random_color():
    a = random.randint(130, 255)
    b = random.randint(130, 255)
    c = random.randint(0, 60)
    rgb = [a, b, c]
    random.shuffle(rgb)
    return f"rgb({rgb[0]}, {rgb[1]}, {rgb[2]})"

def get_question(id: str):
    result = execute_db_query("SELECT * FROM questions WHERE id = ?", (id, ), True)
    if not result:
        raise HTTPException(status_code=404, detail="Question not found")
    return result[0]


def get_team(table: str, team_name: str):
    result = execute_db_query(f"SELECT * FROM {table} WHERE name = ?", (team_name,), True)
    if not result:
        raise HTTPException(status_code=404, detail="Team not found")
    return result[0]


def update_team_score(table: str, team_name: str, score: int, solved_questions: int):
    execute_db_query(
        f"UPDATE {table} SET score = ?, solved_questions = ? WHERE name = ?", 
        (score, solved_questions, team_name)
    )

def log_submission(is_correct: bool, team_name: str, answer: str, id: str, correct_answer: str, score: Optional[int] = None):
    if is_correct:
        logging.info(
            f"{team_name} submitted {answer} for id {id}. Correct answer is {correct_answer}. "
            f"Current score is {score}."
        )
    else:
        logging.info(
            f"{team_name} submitted {answer} for id {id}. Correct answer is {correct_answer}. "
            f"Score remains unchanged."
        )

class Table(BaseModel):
    name: str

class Generator(BaseModel):
    topic: str
    num: int

class QuickSignUp(BaseModel):
    name: str

class Signup(BaseModel):
    team_name: str
    password: str

class Answer(BaseModel):
    id: str
    answer: str
    team_name: str
    table: str

# Define a Settings model with the JWT secret key
class Settings(BaseModel):
    authjwt_secret_key: str = "your-secret-key"

# Load the JWT configuration from the Settings model
@AuthJWT.load_config
def get_config():
    return Settings()

# Define a User model for login request validation
class User(BaseModel):
    team_name: str
    password: str

@app.get("/test")
async def test(request: Request):
      return {"message":"This is a test"}

@app.get("/get_teams_table")
async def get_teams_table(table_name: Optional[str] = "teams"):
    teams = execute_db_query(f"SELECT * FROM {table_name}")
    return {"teams": teams}


@app.post("/submit_answer")
async def submit_answer(a: Answer, db_name: Optional[str] = "database.db", Authorize: AuthJWT = Depends()):
    if os.getenv("TESTING") != "True":
        Authorize.jwt_required()
    try:
        question = get_question(a.id)
        is_correct = question[1] == a.answer or similar(question[1], a.answer)

        if is_correct:
            team = get_team(a.table, a.team_name)
            solved_questions = team[3] + 1
            score = team[2] + question[2]

            update_team_score(a.table, a.team_name, score, solved_questions)
            log_submission(is_correct, a.team_name, a.answer, a.id, question[1], score)
            return {"message": "Correct"}

        log_submission(is_correct, a.team_name, a.answer, a.id, question[1])
        return {"message": "Incorrect", "correct_answer": question[1]}
    except HTTPException as e:
        raise e
    except Exception as e:
        logging.error("Error occurred when submitting answer", exc_info=True)
        raise HTTPException(status_code=500, detail="An error occurred when submitting the answer.")


@app.post("/quick_signup")  
async def quick_signup(team: QuickSignUp, Authorize: AuthJWT = Depends()):
    team_name = team.name
    team_color = random_color()

    existing_team = execute_db_query("SELECT * FROM teams WHERE name = ?", (team_name,), fetchone=True)
    if existing_team is not None:
        return {"message": "Team already exists"}

    # Create a new team
    execute_db_query("INSERT INTO teams VALUES (?, ?, ?, ?, ?)", (team_name, 0, 0, 0, team_color))

    access_token = Authorize.create_access_token(subject=team_name)
    return {"access_token": access_token}



@app.post("/signup")
async def signup(user: Signup, Authorize: AuthJWT = Depends()):
    team_name = user.team_name
    password = user.password
    team_color = random_color()

    # Check if team_name is in teams table
    existing_team = execute_db_query("SELECT * FROM teams WHERE name = ?", (team_name,), fetchone=True, db="comp.db")
    if existing_team is not None:
        return {"message": "Team already exists"}

    # Create a new team
    execute_db_query("INSERT INTO teams VALUES (?, ?, ?, ?, ?)", (team_name, password, 0, 0, team_color)) 
    access_token = Authorize.create_access_token(subject=team_name)
    return {"access_token": access_token}