# README.md

## FastAPI Quiz Application

This is a simple Quiz application built using the FastAPI framework. It provides endpoints for managing quiz activities such as getting teams data, submitting answers, and quick signup.

## Table of Contents

- [Installation](#installation)
- [Setting Up Virtual Environment](#setting-up-virtual-environment)
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

## Setting Up Virtual Environment

This project uses `Pipfile` and `Pipfile.lock` to manage dependencies in a virtual environment using `pipenv`.

To set up the virtual environment:

1. Install `pipenv` if you haven't:
    ```bash
    pip install pipenv
    ```
    
2. Navigate to the project directory and create a virtual environment and install dependencies:
    ```bash
    pipenv install
    ```

3. To activate the virtual environment:
    ```bash
    pipenv shell
    ```

Now, you can run commands within the virtual environment context. To exit the virtual environment, simply type `exit`.

## Usage

To run this project, you need to set up an SQLite database named `database.db`. Your database should contain at least two tables: `questions` and `grokkers`. The structure of these tables is beyond the scope of this readme. You'll also need to replace `your-secret-key` with your actual secret key for JWT.

You need to set an environment variable `TESTING` that indicates whether you are testing the application or not. 

The logging is set up to store all the logs in `app.log`.

Once you're set, start the application by running:

```bash
uvicorn main:app --reload
```

Replace `main` with the name of your python file.

## API Endpoints

The application provides the following API endpoints:

- `GET /test`: 
  - Description: Used for testing if the API is running.
  - Response: A test message.

- `GET /get_teams_table`: 
  - Description: Fetches all the teams from the given table name.
  - Parameters: `table_name` (optional). Defaults to 'grokkers' if not provided.
  - Response: List of teams from the specified table.

- `GET /get_comp_table`: 
  - Description: Fetches all the teams from the competition table.
  - Response: List of teams from the competition table.

- `POST /submit_answer`: 
  - Description: Submits an answer for a specific question.
  - Body: `Answer` object containing the team's ID, question ID, and the provided answer.
  - Response: If the provided answer is correct, it updates the team's score and solved questions and returns a success message.

- `POST /quick_signup`: 
  - Description: Quickly signs up a team.
  - Body: `QuickSignUp` object containing team details.
  - Response: If the team does not already exist in the 'grokkers' table, it creates a new team and returns an access token.

- `POST /submit_answer_sec`: 
  - Description: Secured endpoint to submit an answer for a specific question with additional security checks.
  - Body: `Answer` object containing the question ID, provided answer, and team's name.
  - Response: If the provided answer is correct, it updates the team's score and solved questions from the competition table, returns a success message, and logs the attempt. If incorrect, it returns the correct answer and logs the attempt. Also, performs various security checks such as checking for duplicate IPs, ensuring that a team does not attempt a question more than once, and ensuring questions are attempted at an acceptable pace.


## License
This project is licensed under the [MIT Licence](https://choosealicense.com/licenses/mit/).
