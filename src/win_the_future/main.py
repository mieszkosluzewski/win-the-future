from fastapi import FastAPI

from win_the_future.api.auth import router as auth_router
from win_the_future.api.days import router as days_router
from win_the_future.api.tasks import router as tasks_router
from win_the_future.api.users import router as users_router

app = FastAPI(
    title="Win The Future",
    version="0.1.0",
)

app.include_router(tasks_router)
app.include_router(days_router)
app.include_router(users_router)
app.include_router(auth_router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
