from sqlalchemy.orm import Session
from app.models.task import Task
from app.schemas.task import TaskCreate, TaskUpdate


class TaskService:
    @staticmethod
    def create_task(db: Session, task_data: TaskCreate, created_by: int) -> Task:
        task = Task(**task_data.model_dump(), created_by=created_by)
        db.add(task)
        db.commit()
        db.refresh(task)
        return task

    @staticmethod
    def get_task(db: Session, task_id: int) -> Task:
        return db.query(Task).filter(Task.id == task_id).first()

    @staticmethod
    def get_all_tasks(db: Session, skip: int = 0, limit: int = 100):
        return db.query(Task).offset(skip).limit(limit).all()

    @staticmethod
    def get_tasks_by_category(db: Session, category: str, skip: int = 0, limit: int = 100):
        return db.query(Task).filter(Task.category == category).offset(skip).limit(limit).all()

    @staticmethod
    def update_task(db: Session, task_id: int, task_data: TaskUpdate) -> Task:
        task = db.query(Task).filter(Task.id == task_id).first()
        if task:
            update_data = task_data.model_dump(exclude_unset=True)
            for key, value in update_data.items():
                setattr(task, key, value)
            db.commit()
            db.refresh(task)
        return task

    @staticmethod
    def delete_task(db: Session, task_id: int) -> bool:
        task = db.query(Task).filter(Task.id == task_id).first()
        if task:
            db.delete(task)
            db.commit()
            return True
        return False

    @staticmethod
    def get_categories(db: Session):
        categories = db.query(Task.category).distinct().all()
        return [c[0] for c in categories if c[0]]
