import sqlite3
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List
from contextlib import asynccontextmanager

# Stage 0: Create the database and table, and insert 3 initial tasks if empty
def init_db():
    with sqlite3.connect("tasks.db") as conn:
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                done BOOLEAN NOT NULL CHECK (done IN (0, 1))
            )
        ''')
        cursor.execute("SELECT COUNT(*) FROM tasks")
        if cursor.fetchone()[0] == 0:
            cursor.executemany(
                "INSERT INTO tasks (title, done) VALUES (?, ?)",
                [("Buy milk", 0), ("Finish FlyRank assignment", 0), ("Read a book", 1)]
            )
        conn.commit()

# Run init_db() when the API starts up
@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield

app = FastAPI(
    title="Task API with SQLite",
    lifespan=lifespan,
    description="A CRUD API for managing tasks stored in an SQLite database."
)

class Task(BaseModel):
    title: str
    done: bool = False

class TaskResponse(Task):
    id: int

# Helper to format SQLite rows into Python dictionaries and convert 0/1 to True/False
def dict_factory(cursor, row):
    d = {}
    for idx, col in enumerate(cursor.description):
        val = row[idx]
        if col[0] == 'done':
            val = bool(val)
        d[col[0]] = val
    return d

def get_db():
    conn = sqlite3.connect("tasks.db")
    conn.row_factory = dict_factory
    return conn

@app.get("/")
def read_root():
    return {"name": "Task API", "version": "2.0", "endpoints": ["/tasks"]}

@app.get("/health")
def health_check():
    return {"status": "ok"}

# Stage 1: Read from database
@app.get("/tasks", response_model=List[TaskResponse])
def get_tasks():
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM tasks")
        return cursor.fetchall()

@app.get("/tasks/{task_id}", response_model=TaskResponse)
def get_task(task_id: int):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
        task = cursor.fetchone()
        if task is None:
            raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
        return task

# Stage 2: Create new tasks in database
@app.post("/tasks", response_model=TaskResponse, status_code=201)
def create_task(task: Task):
    if not task.title.strip():
        raise HTTPException(status_code=400, detail="Title cannot be empty")
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO tasks (title, done) VALUES (?, ?)", (task.title, int(task.done)))
        conn.commit()
        task_id = cursor.lastrowid
        cursor.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
        return cursor.fetchone()

# Stage 3: Update and delete
@app.put("/tasks/{task_id}", response_model=TaskResponse)
def update_task(task_id: int, task: Task):
    if not task.title.strip():
        raise HTTPException(status_code=400, detail="Title cannot be empty")
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
        if cursor.fetchone() is None:
            raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
        
        cursor.execute("UPDATE tasks SET title = ?, done = ? WHERE id = ?", (task.title, int(task.done), task_id))
        conn.commit()
        cursor.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
        return cursor.fetchone()

@app.delete("/tasks/{task_id}", status_code=204)
def delete_task(task_id: int):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
        if cursor.fetchone() is None:
            raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
        
        cursor.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
        conn.commit()
