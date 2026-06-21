import asyncio
import logging
from itertools import count

from fastapi import APIRouter, status
from pydantic import BaseModel, Field

from app.core.exceptions import TaskNotFoundError

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/tasks", tags=["tasks"])

# --- In-memory store -------------------------------------------------
# Demo only. In a real service this dict becomes a SQLAlchemy/Postgres
# call. The asyncio.Lock matters even in-process: without it, two
# concurrent POSTs could read the same counter value before either
# writes it back (a classic race condition), and you'd get duplicate IDs.
_tasks: dict[int, "Task"] = {}
_id_counter = count(start=1)
_lock = asyncio.Lock()


class TaskCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    done: bool = False


class Task(TaskCreate):
    id: int


@router.get("", response_model=list[Task])
async def list_tasks() -> list[Task]:
    return list(_tasks.values())


@router.post("", response_model=Task, status_code=status.HTTP_201_CREATED)
async def create_task(payload: TaskCreate) -> Task:
    async with _lock:
        task_id = next(_id_counter)
        task = Task(id=task_id, **payload.model_dump())
        _tasks[task_id] = task
    logger.info(f"Task created: id={task_id} title={task.title!r}")
    return task


@router.get("/{task_id}", response_model=Task)
async def get_task(task_id: int) -> Task:
    task = _tasks.get(task_id)
    if task is None:
        logger.warning(f"Task lookup failed: id={task_id}")
        raise TaskNotFoundError(task_id)
    return task


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(task_id: int) -> None:
    async with _lock:
        if task_id not in _tasks:
            raise TaskNotFoundError(task_id)
        del _tasks[task_id]
    logger.info(f"Task deleted: id={task_id}")
