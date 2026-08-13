from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.db.dependencies import get_db
from app.core.dependencies import get_current_user
from app.schemas.task import TaskCreate, TaskUpdate, TaskResponse
from app.services.task_service import TaskService

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.post("/", response_model=TaskResponse)
def create_task(task_data: TaskCreate, current_user = Depends(get_current_user), db: Session = Depends(get_db)):
    """Create a new task"""
    task = TaskService.create_task(db, task_data, current_user.id)
    return task


@router.get("/{task_id}", response_model=TaskResponse)
def get_task(task_id: int, db: Session = Depends(get_db)):
    """Get a specific task"""
    task = TaskService.get_task(db, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@router.get("/", response_model=list[TaskResponse])
def list_tasks(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    category: str = Query(None),
    db: Session = Depends(get_db)
):
    """List all tasks, optionally filtered by category"""
    if category:
        tasks = TaskService.get_tasks_by_category(db, category, skip, limit)
    else:
        tasks = TaskService.get_all_tasks(db, skip, limit)
    return tasks


@router.put("/{task_id}", response_model=TaskResponse)
def update_task(task_id: int, task_data: TaskUpdate, current_user = Depends(get_current_user), db: Session = Depends(get_db)):
    """Update a task"""
    task = TaskService.get_task(db, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    if task.created_by != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to update this task")
    
    task = TaskService.update_task(db, task_id, task_data)
    return task


@router.delete("/{task_id}")
def delete_task(task_id: int, current_user = Depends(get_current_user), db: Session = Depends(get_db)):
    """Delete a task"""
    task = TaskService.get_task(db, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    if task.created_by != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to delete this task")
    
    success = TaskService.delete_task(db, task_id)
    return {"message": "Task deleted successfully"}


@router.get("/categories/list")
def get_categories(db: Session = Depends(get_db)):
    """Get all task categories"""
    categories = TaskService.get_categories(db)
    return {"categories": categories}
