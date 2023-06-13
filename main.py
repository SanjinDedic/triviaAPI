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
                if '.github.io' in origin or '.repl.co' in origin or origin.startswith('https://replit.com'):
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
def execute_db_query(query, params=()):
    try:
        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        c.execute(query, params)
        result = c.fetchall()
        conn.commit()
    except Exception as e:
        logging.error("Error occurred when executing database query", exc_info=True)
        raise e
    finally:
        conn.close()
    return result

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

class Table(BaseModel):
    name: str

class Generator(BaseModel):
    topic: str
    num: int

class QuickSignUp(BaseModel):
    name: str

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
async def get_teams_table(table_name: Optional[str] = "grokkers"):
    teams = execute_db_query(f"SELECT * FROM {table_name}")
    return {"teams": teams}

@app.post("/submit_answer")
async def submit_answer(a: Answer, Authorize: AuthJWT = Depends()):
    if os.getenv("TESTING") != "True":
        Authorize.jwt_required()
    
    try:
        # Retrieve the question
        question = execute_db_query("SELECT * FROM questions WHERE id = ?", (a.id, ))
        if not question:
            return {"message": "Question not found"}
        question = question[0]
        
        if question[1] == a.answer or similar(question[1], a.answer):
            pts = question[2]
            # Retrieve the team data
            team = execute_db_query("SELECT * FROM {} WHERE name = ?".format(a.table), (a.team_name, ))
            if not team:
                return {"message": "Team not found"}
            team = team[0]
            
            # Update the solved questions and score
            solved_questions = team[3] + 1
            score = team[2] + pts
            execute_db_query("UPDATE {} SET score = ?, solved_questions = ? WHERE name = ?".format(a.table), (score, solved_questions, a.team_name))
            logging.info(f"{a.team_name} submitted {a.answer} for id {a.id}. Correct answer is {question[1]}. Current score is {score}.")
            return {"message": "Correct"}
        else:
            logging.info(f"{a.team_name} submitted {a.answer} for id {a.id}. Correct answer is {question[1]}. Score remains unchanged.")
            return {"message": "Incorrect", "correct_answer": question[1]}
    except Exception as e:
        logging.error("Error occurred when submitting answer", exc_info=True)
        raise HTTPException(status_code=500, detail="An error occurred when submitting the answer.")


@app.post("/quick_signup")  
async def quick_signup(team: QuickSignUp, Authorize: AuthJWT = Depends()):
    team_name = team.name
    team_color = random_color()
    team_password = 'Tldce54342'
    conn = sqlite3.connect('database.db')
    c = conn.cursor()

    #check if team_name is in grokkers table
    c.execute("SELECT * FROM grokkers WHERE name = ?", (team_name,))
    existing_team_grokkers = c.fetchone()
    if existing_team_grokkers is not None:
        return {"message": "Team already exists"}

    # Create a new team
    c.execute("INSERT INTO grokkers VALUES (?, ?, ?, ?, ?)", (team_name, team_password, 0, 0, random_color())) 
    conn.commit()
    access_token = Authorize.create_access_token(subject=team_name)
    return {"access_token": access_token}
