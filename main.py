from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
import sqlite3
import json
from typing import Optional
from fastapi import Depends, FastAPI, HTTPException
from fastapi_jwt_auth import AuthJWT
from fastapi_jwt_auth.exceptions import AuthJWTException
from typing import List, Dict
from validator import *

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

class SaveJSON(BaseModel):
    quiz_data: List[Dict]
    filename: str

class SignUp(BaseModel):
    name: str
    password: str

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

# Login endpoint
@app.post("/login")
async def login(user: User, Authorize: AuthJWT = Depends()):
    # Connect to the SQLite database
    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    # Query the database to find a team with the given name and password
    c.execute("SELECT * FROM teams WHERE name = ? AND password = ?", (user.team_name, user.password))
    team = c.fetchone()

    # If no team is found, raise an HTTP 401 error
    if team is None:
        raise HTTPException(status_code=401, detail="Invalid team name or password")

    # If a team is found, create a JWT token with the team name as the subject
    access_token = Authorize.create_access_token(subject=user.team_name)
    return {"access_token": access_token}

@app.get("/test")
async def test(request: Request):
      return {"message":"This is a test"}

@app.get("/")
async def home():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("SELECT * FROM questions")
    questions = c.fetchall()
    return {"length": len(questions)}
    

from typing import Optional

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
        return {"message": "Correct"}
    else:
        return {"message": "Incorrect"}


@app.post("/save_json")
async def save_json(request: SaveJSON):
    data = request.quiz_data
    filename = request.filename
    with open(f"quizzes/{filename}.json", "w") as f:
        json.dump(data, f)
    return {"message": "File saved successfully"}


@app.post("/signup")
async def signup(team: SignUp):
    team_name = team.name
    team_password = team.password
    team_color = random_color()

    conn = sqlite3.connect('database.db')
    c = conn.cursor()

    # Check if the team already exists
    c.execute("SELECT * FROM teams WHERE name = ?", (team_name,))
    existing_team = c.fetchone()

    if existing_team is not None:
        return {"message": "Team already exists"}

    # Create a new team
    c.execute("INSERT INTO teams (name, password, score, solved_questions, color) VALUES (?, ?, 0, ?, ?)",
              (team_name, team_password, json.dumps([]), team_color))
    conn.commit()

    return {"message": "Team created successfully"}



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



@app.post("/generate_quiz")
async def generate(generator: Generator):
   topic_name= generator.topic
   qs_number= generator.num
   generated_json= create_quiz(topic=topic_name, num=qs_number)
   return generated_json
