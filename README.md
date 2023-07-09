# README.md

## FastAPI Quiz Application

This is a simple Quiz application built using the FastAPI framework. It provides endpoints for managing quiz activities such as getting teams data, submitting answers, and quick signup.

## Table of Contents

- [Installation](#installation)
- [Usage](#usage)
- [API Endpoints](#api-endpoints)
- [License](#license)

## Installation

Before you can run this application, make sure you have the following installed:

- Python 3.6+
- FastAPI

Clone the repository and navigate into the project directory. Use the package manager [pip](https://pip.pypa.io/en/stable/) to install the necessary packages. 

```bash
pip install fastapi
pip install uvicorn[standard]
pip install pydantic
pip install sqlite3
pip install fastapi-jwt-auth
```

You can then start the application by running:

```bash
uvicorn main:app --reload
```

Replace `main` with the name of your python file.

## Usage

To run this project, you need to set up an SQLite database named `database.db`. Your database should contain at least two tables: `questions` and `grokkers`. The structure of these tables is beyond the scope of this readme. You'll also need to replace `your-secret-key` with your actual secret key for JWT.

You need to set an environment variable `TESTING` that indicates whether you are testing the application or not. 

The logging is set up to store all the logs in `app.log`.

## API Endpoints

The application provides the following API endpoints:

- `GET /test`: Returns a test message
- `GET /get_teams_table`: Returns all the teams from the given table name. If no table name is provided, it defaults to the table 'grokkers'
- `POST /submit_answer`: Takes an Answer object and validates it. If the provided answer is correct, it updates the team's score and solved questions.
- `POST /quick_signup`: Takes a QuickSignUp object and creates a new team in the 'grokkers' table if it does not already exist. It then returns an access token.

## License
This project is licensed under the [MIT Licence](https://choosealicense.com/licenses/mit/).
