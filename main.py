from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
import sqlite3
import json
import os
from typing import Optional
from fastapi import Depends, FastAPI, HTTPException
from fastapi_jwt_auth import AuthJWT
from fastapi_jwt_auth.exceptions import AuthJWTException
from difflib import SequenceMatcher
from typing import Optional

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_methods=["*"],
    allow_headers=["*"],
)
'''
async def custom_allow_origin(request: Request, call_next):
    allow_origin = False
    origin = request.headers.get('origin', None)
    # Log the origin
    with open("origins.txt", "a") as file:
        file.write(f"Origin: {origin}\n")


    if origin:
        if '.github.io' in origin or '.repl.co' in origin or origin.startswith('https://replit.com'):
            allow_origin = True

    if allow_origin:
        response = await call_next(request)
    else:
        response = Response(content="CORS not allowed", status_code=400)

    return response

app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.middleware('http')(custom_allow_origin)
'''

def similar(s1, s2, threshold=0.6):
    similarity_ratio = SequenceMatcher(None, s1, s2).ratio()
    return similarity_ratio >= threshold

def update_log(team_name, team_answer, correct_answer, score):
    log_file = os.path.join(os.getcwd(), 'logs', 'log.txt')
    with open(log_file, 'a') as f:
        f.write(f"{team_name} submitted {team_answer}. Correct answer is {correct_answer}. Current score is {score}.\n")

def random_color():
    #2/3 colors will have values higher than 130 and 1/3 will be lower than 60
    import random
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

# Load the JWT configuration from the Settings mode
@AuthJWT.load_config
def get_config():
    return Settings()

# Define a User model for login request validation
class User(BaseModel):
    team_name: str
    password: str

# Define a User model for login request validation
@app.get("/test")
async def test(request: Request):
      return {"message":"This is a test"}

@app.get("/get_teams_table")
async def get_teams_table(table_name: Optional[str] = "grokkers"):
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute(f"SELECT * FROM {table_name}")
    teams = c.fetchall()
    conn.close()
    return {"teams": teams}


#just need to figure out how to get the solved questions list updated in the database
@app.post("/submit_answer")
async def submit_answer(a: Answer, Authorize: AuthJWT = Depends()):
    Authorize.jwt_required()
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("SELECT * FROM questions WHERE id = ?", (a.id,))
    question = c.fetchone()
    if question == None:
        return {"message": "Question not found"}  
    elif question[1] == a.answer or similar(question[1], a.answer):
        print(question[1], a.answer)
        pts = question[2]
        print(pts)
        #update the database table denoted by a.table
        #add pts to the score for the team and increment the solved questions
        c.execute(f"SELECT * FROM {a.table} WHERE name = ?", (a.team_name,))

        team = c.fetchone()
        solved_questions = team[3]
        solved_questions += 1
        score = team[2]
        score += pts
        c.execute(f"UPDATE {a.table} SET score = ?, solved_questions = ? WHERE name = ?", (score, solved_questions, a.team_name))
        conn.commit()
        update_log(team_name=a.team_name, team_answer=a.answer, correct_answer=question[1], score=score)
        return {"message": "Correct"}
    else:
        update_log(team_name=a.team_name, team_answer=a.answer, correct_answer=question[1], score=score)
        return {"message": "Incorrect"}


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