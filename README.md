# Task API with SQLite Database - FlyRank W3

A simple CRUD API for managing tasks, upgraded to persist data using a real SQLite database. 

## Database Details
* **Why SQLite was chosen:** It is lightweight, requires no separate server setup, and stores all data locally in a single file, making it perfect for an introductory persistent API.
* **Storage Location:** The database is stored locally in the root directory as `tasks.db`. The file and the `tasks` table are created automatically on the first run.
* **Example SQL Query executed:** `SELECT * FROM tasks WHERE done = 1;`

## Run Instructions
1. Install dependencies: `pip install fastapi uvicorn`
2. Start the server: `uvicorn main:app --reload`
3. View the interactive Swagger UI at: `http://localhost:8000/docs`
