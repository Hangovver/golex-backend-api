"""
User Schemas
Pydantic models for user-related API requests/responses
"""
from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime


class UserBase(BaseModel):
    """Base user schema"""
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=50)
    full_name: Optional[str] = None


class UserCreate(UserBase):
    """Schema for user registration"""
    password: str = Field(..., min_length=8, max_length=100)


class UserLogin(BaseModel):
    """Schema for user login"""
    username: str  # Can be email or username
    password: str


class UserResponse(UserBase):
    """Schema for user response"""
    id: int
    is_active: bool
    created_at: datetime
    last_login: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class Token(BaseModel):
    """Schema for token response"""
    access_token: str
    refresh_token: str
    token_type: str


class TokenData(BaseModel):
    """Schema for token payload"""
    sub: int  # User ID
    exp: Optional[datetime] = None


class FavoriteCreate(BaseModel):
    """Schema for creating a favorite"""
    entity_type: str = Field(..., pattern="^(team|player|league|match)$")
    entity_id: int
    entity_name: str
    notify_matches: bool = True
    notify_goals: bool = True
    notify_news: bool = False


class FavoriteResponse(BaseModel):
    """Schema for favorite response"""
    id: int
    entity_type: str
    entity_id: int
    entity_name: str
    notify_matches: bool
    notify_goals: bool
    notify_news: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


class FavoriteUpdate(BaseModel):
    """Schema for updating favorite settings"""
    notify_matches: Optional[bool] = None
    notify_goals: Optional[bool] = None
    notify_news: Optional[bool] = None

