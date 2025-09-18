from pydantic import BaseModel
from typing import Optional

# --- Token Schemas ---
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

# --- User Schemas ---
class UserBase(BaseModel):
    username: str

class UserCreate(UserBase):
    password: str
    role: str

class User(UserBase):
    id: str
    role: str

    class Config:
        orm_mode = True

# --- Camera Schemas ---
class CameraBase(BaseModel):
    name: str
    location: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None

class CameraCreate(CameraBase):
    pass

class Camera(CameraBase):
    id: str

    class Config:
        orm_mode = True

# --- AI Schemas ---
class AIRequest(BaseModel):
    query: str
