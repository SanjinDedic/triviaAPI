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

testing = False

# Allowed origins for CORS
allowed_origins = [
    "https://aitrivia.live",
    "https://*.repl.co",
    "https://*.cloudfront.net",
    "http://127.0.0.2:5500",
    "http://localhost"
]

if testing:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=['*'],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
else:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


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

def get_question(id: str, db: str = "trivia.db"):
    result = execute_db_query("SELECT * FROM questions WHERE id = ?", (id, ), fetchone=False, db=db)
    if not result:
        raise HTTPException(status_code=404, detail="Question not found")
    return result[0]


def get_team(team_name: str, db: str = "trivia.db"):
    result = execute_db_query(f"SELECT * FROM teams WHERE name = ?", (team_name,), fetchone=False, db=db)
    if not result:
        raise HTTPException(status_code=404, detail="Team not found")
    return result[0]


def update_team(name: str, score: int, solved_qs: int, attempted_qs: int, db: str):
    execute_db_query(
        f"UPDATE teams SET score = ?, solved_questions = ?, attempted_questions = ? WHERE name = ?", 
        params=(score, solved_qs, attempted_qs, name),fetchone=False, db=db 
    )

def update_attempted_questions(name: str, ip: str, question_id: str, solved: bool):
  execute_db_query(
    f"INSERT INTO attempted_questions VALUES (?, ?, ?, ?, ?)",
    params=(name, ip, question_id, datetime.now(), solved), fetchone=False, db="comp.db"
  )

def security_validation(name: str, question: str):
    #check if there are multiple teams with the same ip
    print("checking if allowed")
    result = execute_db_query("SELECT * FROM teams WHERE name = ?", (name, ), fetchone=True, db="comp.db")
    if result is None:
        print("team not found")
        return {"security error": "team not found"}
    team_ip = result[1]
    print("team ip", team_ip)
    result = execute_db_query("SELECT * FROM teams WHERE ip = ?", (team_ip, ), fetchone=False, db="comp.db")

    if len(result) > 1:
        print("duplicate ip")
        return {"security error": "duplicate ip"}
    #check if the question has been attempted by the team 
    result = execute_db_query("SELECT * FROM attempted_questions WHERE team_name = ? AND question_id = ?", (name, question), fetchone=False, db="comp.db")
    if len(result) > 0:
        print("question already attempted")
        return {"security error": "question already attempted"}
    #define the timestamp for the most recent question attempt
    result = execute_db_query("SELECT * FROM attempted_questions WHERE team_name = ? ORDER BY timestamp DESC", (name, ), fetchone=True, db="comp.db")
    if result:
        recent_timestamp = result[3]
        if (datetime.now() - datetime.strptime(recent_timestamp, "%Y-%m-%d %H:%M:%S.%f")).total_seconds() > 60:
            print("too soon")
            return {"security error": "irregular question timing"}
    else:
        print("no recent timestamp")
    #define the timestamp for the least recent question attempt
    result = execute_db_query("SELECT * FROM attempted_questions WHERE team_name = ? ORDER BY timestamp ASC", (name, ), fetchone=True, db="comp.db")
    if result:
        first_timestamp = result[3]
        #if first timestamp is older than 6 minutes return security error
        if (datetime.now() - datetime.strptime(first_timestamp, "%Y-%m-%d %H:%M:%S.%f")).total_seconds() > 360:
            print("too late")
            return {"security error": "quiz has ended"}
    else:
        print("no first timestamp")
    #check if the total number of questions attempted by a team is more than 10
    result = execute_db_query("SELECT * FROM attempted_questions WHERE team_name = ?", (name, ), fetchone=False, db="comp.db")
    if result:
        if len(result) > 10:
            return {"security error": "more than 10 question attempts"}
    else:
        print("no attempts")

    return True
    

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

class Answer(BaseModel):
    id: str
    answer: str
    team_name: str

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
async def get_teams_table():
    teams = execute_db_query(f"SELECT * FROM teams", db="trivia.db")
    return {"teams": teams}


@app.get("/get_comp_table")
async def get_comp_table():
    teams = execute_db_query(f"SELECT * FROM teams", db="comp.db")
    return {"teams": teams}

@app.post("/submit_answer")
async def submit_answer(a: Answer, Authorize: AuthJWT = Depends()):
    if os.getenv("TESTING") != "True":
        Authorize.jwt_required()
    try:
        correct_ans, question_pts = get_question(id=a.id, db="trivia.db" )[2:4]
        team_ip, score, attempted_qs, solved_qs = get_team(team_name=a.team_name, db="trivia.db")[1:5]
        is_correct = a.answer == correct_ans or similar(correct_ans, a.answer)
        if is_correct:
            score += question_pts
            solved_qs += 1
            attempted_qs += 1
            update_team(name=a.team_name, score=score, solved_qs=solved_qs, attempted_qs=attempted_qs, db="trivia.db")
            log_submission(is_correct, a.team_name, a.answer, a.id, correct_ans, score)
            return {"message": "Correct"}
        attempted_qs += 1
        log_submission(is_correct, a.team_name, a.answer, a.id, correct_ans)
        update_team(name=a.team_name, score=score, solved_qs=solved_qs, attempted_qs=attempted_qs, db="trivia.db")
        return {"message": "Incorrect", "correct_answer": correct_ans}
    except HTTPException as e:
        raise e
    except Exception as e:
        logging.error("Error occurred when submitting answer", exc_info=True)
        raise HTTPException(status_code=500, detail="An error occurred when submitting the answer.")


@app.post("/submit_answer_sec")
async def submit_answer(a: Answer, Authorize: AuthJWT = Depends()):
    if os.getenv("TESTING") != "True":
        Authorize.jwt_required()
    try:
        correct_ans, question_pts = get_question(id=a.id, db="comp.db")[2:4]
        print("correct ans found",correct_ans)
        team_ip, score, attempted_qs, solved_qs = get_team(team_name=a.team_name, db="comp.db")[1:5]
        print("team fetched")
        is_correct = a.answer == correct_ans or similar(correct_ans, a.answer)
        print("correct status", is_correct)
        security_check = security_validation(a.team_name, a.id)
        if security_check != True:
            print("security check failed")
            return security_check
        
        attempted_qs += 1
        print('reached far')
        if is_correct:
            score += question_pts
            solved_qs += 1
            log_submission(is_correct, a.team_name, a.answer, a.id, correct_ans)
            print('attempting logging')
            update_team(name=a.team_name, score=score, solved_qs=solved_qs, attempted_qs=attempted_qs, db="comp.db")
            update_attempted_questions(name=a.team_name, ip=team_ip, question_id=a.id, solved=is_correct)
            return {"message": "Correct"}
        log_submission(is_correct, a.team_name, a.answer, a.id, correct_ans)
        update_team(name=a.team_name, score=score, solved_qs=solved_qs, attempted_qs=attempted_qs, db="comp.db")
        update_attempted_questions(name=a.team_name, ip=team_ip, question_id=a.id, solved=is_correct)

        return {"message": "Incorrect", "correct_answer": correct_ans}
    except HTTPException as e:
        raise e
    except Exception as e:
        logging.error("Error occurred when submitting answer", exc_info=True)
        raise HTTPException(status_code=500, detail="An error occurred when submitting the answer.")



@app.post("/quick_signup")  #only possible for Trivia
async def quick_signup(team: QuickSignUp, Authorize: AuthJWT = Depends()):
    team_color = random_color()

    existing_team = execute_db_query("SELECT * FROM teams WHERE name = ?", (team.name,), fetchone=True, db="trivia.db")
    if existing_team is not None:
        return {"message": "Team already exists"}

    # Create a new team
    execute_db_query("INSERT INTO teams VALUES (?, ?, ?, ?, ?, ?)", (team.name,'', 0, 0, 0, team_color))

    access_token = Authorize.create_access_token(subject=team.name)
    return {"access_token": access_token}



@app.post("/quick_signup_sec")
async def quick_signup(team: QuickSignUp, request: Request, Authorize: AuthJWT = Depends()):
    team_color = random_color()
    print("team color", team_color)
    # Get client IP address
    client_ip = request.client.host
    print("client ip", client_ip)
    existing_team = execute_db_query("SELECT * FROM teams WHERE name = ?", (team.name,), fetchone=True, db="comp.db")
    if existing_team is not None:
        return {"message": "Team already exists"}
    #check if there is another team with the same IP
    existing_team = execute_db_query("SELECT * FROM teams WHERE ip = ?", (client_ip,), fetchone=True, db="comp.db")
    if existing_team is not None:
        return {"message": "Another team already exists with the same IP address"}
    print("team about to be created")
    # Create a new team and include the IP address
    execute_db_query("INSERT INTO teams (name, ip, score, attempted_questions, solved_questions, color) VALUES (?, ?, ?, ?, ?, ?)", (team.name, client_ip, 0, 0, 0, team_color), db="comp.db")

    access_token = Authorize.create_access_token(subject=team.name)
    return {"access_token": access_token}
