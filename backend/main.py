from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy.orm import Session
import data_models.db_models as models
from data_models.api_models import *
from data_models.db_models import SessionLocal
from sqlalchemy import and_, func

app = FastAPI()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.get("/chickens/")
def get_chickens(db: Session = Depends(get_db)):
    """Просмотр таблицы Chickens"""
    chickens = db.query(models.Chickens).all()
    return {"chickens": chickens}


@app.get("/chickens/{batch_id}")
def get_batch_info(batch_id: str, db: Session = Depends(get_db)):
    """Просмотр параметров партии по batch_id"""
    batch_info = db.query(models.Chickens).get(batch_id)
    return {"batch_info": batch_info}


@app.post("/chickens/")
def add_chikens(new_chickens: Chickens, db: Session = Depends(get_db)):
    db_chikens = models.Chickens(**new_chickens.dict())
    db.add(db_chikens)
    db.commit()
    return {"message": "Chicken's information added successfully"}


@app.put("/chickens/{batch_id}/{field}/{new_value}")
def update_chickens(batch_id: str, field: str, new_value: str, db: Session = Depends(get_db)):
    """Изменение информации о камере"""
    row = db.query(models.Chickens).get(batch_id)
    if row:
        if field == 'count':
            row.count = new_value
        elif field == 'machine_id':
            row.machine_id = new_value
        elif field == 'line_number':
            row.line_number = new_value
        elif field == 'cross_':
            row.cross_ = new_value
        else:
            return {'error': 'Поле не найдено'}
        db.commit()
        return {"message": "Chicken's information added successfully"}
    raise HTTPException(status_code=404, detail="Chicken information not found")


@app.put("/chickens/{start}/{end}/")
def update_time(batch_id: str, start: str, end: str, db: Session = Depends(get_db)):
    """Изменение времени начала и окончания"""
    row = db.query(models.Chickens).get(batch_id)
    if row:
        row.start_time = start
        row.end_time = end
        db.commit()
        return {"message": "Chicken's information added successfully"}
    raise HTTPException(status_code=404, detail="Chicken information not found")


@app.post("/camera/")
def create_camera(camera: Camera, db: Session = Depends(get_db)):
    """Подключение к rtsp-потоку"""
    try:
        db_camera = models.Camera(**camera.dict())
        db.add(db_camera)
        db.commit()
        return {"message": "Camera created successfully"}
    except IntegrityError:
        raise HTTPException(status_code=400, detail="Camera with this name already exists")


@app.get("/camera/")
def get_cameras(db: Session = Depends(get_db)):
    """Просмотр списка всех камер"""
    cameras = db.query(models.Camera).all()
    return {"cameras": cameras}


@app.get("/count/{start_time}/{end_time}")
def count_period(start_time: str, end_time: str, db: Session = Depends(get_db)):
    """Просмотр таблицы Chickens"""
    count = db.query(func.sum(models.Chickens.count)).filter(
        and_(models.Chickens.start_time >= start_time, models.Chickens.end_time <= end_time))
    total = count.scalar()
    return {"count": total}


@app.put("/camera/{camera_id}")
def update_camera(camera_id: int, camera: Camera, db: Session = Depends(get_db)):
    """Изменение информации о камере"""
    db_camera = db.query(models.Camera).filter(models.Camera.camera_id == camera_id).first()
    if db_camera:
        for var, value in vars(camera).items():
            setattr(db_camera, var, value) if value else None
        db.commit()
        return {"message": "Camera updated successfully"}
    raise HTTPException(status_code=404, detail="Camera not found")


@app.delete("/camera/{camera_id}")
def delete_camera(camera_id: int, db: Session = Depends(get_db)):
    db_camera = db.query(models.Camera).filter(models.Camera.camera_id == camera_id).first()
    if db_camera:
        db.delete(db_camera)
        db.commit()
        return {"message": "Camera deleted successfully"}
    raise HTTPException(status_code=404, detail="Camera not found")
