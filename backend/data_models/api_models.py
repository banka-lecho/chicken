from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class Chickens(BaseModel):
    batch_id: str
    start_time: datetime
    end_time: datetime
    line_number: int
    machine_id: int
    count: int
    cross_: str


class Camera(BaseModel):
    camera_id: int
    name: str
    description: Optional[str] = None
    rtsp_stream: Optional[str] = None
