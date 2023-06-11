import os, sqlite3
import json

import subprocess
import sys
import pkg_resources

def install(package):
    subprocess.check_call([sys.executable, "-m", "pip", "install", package])

installed_packages = {pkg.key for pkg in pkg_resources.working_set}

if "fastapi-jwt-auth" not in installed_packages:
    print("Installing required package: fastapi-jwt-auth")
    install("fastapi-jwt-auth")
    print("Package installed successfully")



if os.path.exists('database.db'):
    os.remove('database.db')
    print("Database deleted and recreated")
else:
    print("Dtabase created")
conn = sqlite3.connect('database.db')
c = conn.cursor()
c.execute('''CREATE TABLE questions
                (id text, answer text, points integer)''')

#add the questions to the database by reading the questions.json file
with open('questions.json') as f:
    questions = json.load(f)

for q in questions:
    print(q)
    print(q['id'], q['answer'], q['points'])
    c.execute("INSERT INTO questions VALUES (?, ?, ?)", (q['id'], q['answer'], q['points']))




c.execute('''CREATE TABLE teams
                (name text, password text, score integer, solved_questions integer, color text)''')

c.execute('''CREATE TABLE grokkers
                (name text, password text, score integer, solved_questions integer, color text)''')



#add the teams to the database

def random_color():
    #return a random cloor in hex, make the brightness of each Color > 120
    import random
    r = random.randint(80, 255)
    g = random.randint(80, 255)
    b = random.randint(80, 255)
    return f"#{r:02x}{g:02x}{b:02x}"



c.execute("INSERT INTO teams VALUES (?, ?, ?, ?, ?)", ('Mount Waverley', 'abc', 0, 0, random_color()))
c.execute("INSERT INTO teams VALUES (?, ?, ?, ?, ?)", ('Box Hill', 'abc', 0, 0, random_color()))
c.execute("INSERT INTO teams VALUES (?, ?, ?, ?, ?)", ('Melbourne High', 'abc', 0, 0, random_color()))
c.execute("INSERT INTO teams VALUES (?, ?, ?, ?, ?)", ('Wantirna', 'abc', 0, 0, random_color()))
c.execute("INSERT INTO teams VALUES (?, ?, ?, ?, ?)", ('GitTest', 'git', 0, 0, random_color()))


conn.commit()
conn.close()

print('Database created successfully')
