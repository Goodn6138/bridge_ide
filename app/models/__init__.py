from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class CodeExecutionRequest(BaseModel):
    """Request model for code execution"""
    code: str
    language: Optional[str] = None
    filename: Optional[str] = None
    stdin: Optional[str] = None


class CodeExecutionResult(BaseModel):
    """Result model for code execution"""
    success: bool
    output: Optional[str] = None
    error: Optional[str] = None
    stdout: Optional[str] = None
    stderr: Optional[str] = None
    time: Optional[float] = None
    memory: Optional[int] = None
    token: Optional[str] = None
    status: Optional[dict] = None


class GithubAuthRequest(BaseModel):
    """GitHub OAuth callback code"""
    code: str


class GithubUser(BaseModel):
    """GitHub user model"""
    id: int
    login: str
    name: Optional[str] = None
    email: Optional[str] = None
    avatar_url: Optional[str] = None
    profile_url: Optional[str] = None


class AuthResponse(BaseModel):
    """Authentication response"""
    success: bool
    user: Optional[GithubUser] = None
    token: Optional[str] = None
    error: Optional[str] = None
