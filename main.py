from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

# Root endpoint
@app.get("/")
def read_root():
    return {"message": "GoalAction MCP Server is running!"}

class GoalInput(BaseModel):
    goal: str

@app.post("/plan")
def create_plan(data: GoalInput):
    goal = data.goal
    steps = [
        {"step": "Analyze goal", "link": "https://example.com/analyze"},
        {"step": "Break into tasks", "link": "https://example.com/tasks"},
        {"step": "Execute with resources", "link": "https://example.com/resources"}
    ]
    return {"goal": goal, "plan": steps}
