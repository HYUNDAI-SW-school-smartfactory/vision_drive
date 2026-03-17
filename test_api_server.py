from datetime import datetime
from typing import List

from fastapi import FastAPI, File, UploadFile
from pydantic import BaseModel


app = FastAPI(title="AGV Vision Test API")


class RouteUpdate(BaseModel):
    route: List[str]


route_state: List[str] = ["A", "D", "F"]


@app.get("/health")
def health():
    return {"status": "ok", "time": datetime.now().isoformat()}


@app.get("/command")
def get_command():
    print(f"[GET /command] route={route_state}")
    return {"route": route_state}


@app.post("/command")
def set_command(payload: RouteUpdate):
    global route_state
    route_state = payload.route
    print(f"[POST /command] new_route={route_state}")
    return {"message": "route updated", "route": route_state}


@app.post("/analyze")
async def analyze(file: UploadFile = File(...)):
    content = await file.read()
    print(
        f"[POST /analyze] filename={file.filename}, "
        f"content_type={file.content_type}, size={len(content)} bytes"
    )
    return {
        "message": "image received",
        "filename": file.filename,
        "size_bytes": len(content),
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("test_api_server:app", host="0.0.0.0", port=8000, reload=False)
