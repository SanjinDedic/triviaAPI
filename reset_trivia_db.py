import os, sqlite3
import json

if os.path.exists('trivia.db'):
    os.remove('database.db')
    print("Database deleted and recreated")
else:
    print("Dtabase created")
conn = sqlite3.connect('trivia.db')
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


c.execute('''CREATE TABLE teams(
                name text, 
                score integer, 
                attempted_questions integer,
                solved_questions integer, 
                color text)''')


conn.commit()
conn.close()

print('Database created successfully')
