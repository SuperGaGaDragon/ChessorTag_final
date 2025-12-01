from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session
import random

from .db import get_db
from .auth_models import User
from .auth_utils import (
    hash_password,
    verify_password,
    create_access_token,
    SECRET_KEY,
    ALGORITHM,
)

router = APIRouter(
    prefix="/api/auth",
    tags=["auth"],
)


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    username: str | None = None


class RegisterResponse(BaseModel):
    access_token: str
    user_id: str
    email: str
    username: str | None = None


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


@router.post("/register", response_model=RegisterResponse)
def register(req: RegisterRequest, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == req.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered.")

    # Randomly assign avatar (loading3.png or loading4.png)
    avatar = random.choice(["assets/loading3.png", "assets/loading4.png"])

    hashed_pw = hash_password(req.password)
    new_user = User(
        email=req.email,
        username=req.username,
        avatar=avatar,
        hashed_password=hashed_pw,
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    token = create_access_token(
        user_id=new_user.id,
        email=new_user.email,
    )
    return RegisterResponse(
        access_token=token,
        user_id=new_user.id,
        email=new_user.email,
        username=new_user.username,
    )


@router.post("/login", response_model=RegisterResponse)
def login(req: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == req.email).first()
    if not user or not verify_password(req.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials"
        )

    token = create_access_token(user_id=user.id, email=user.email)
    return RegisterResponse(access_token=token, user_id=user.id, email=user.email, username=user.username)


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


def get_current_user(db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str | None = payload.get("sub")
    except JWTError:
        raise credentials_exception

    if user_id is None:
        raise credentials_exception

    user = db.get(User, user_id)
    if user is None:
        raise credentials_exception
    return user


class UserProfileResponse(BaseModel):
    user_id: str
    email: str
    username: str | None = None
    avatar: str | None = None


class UpdateUsernameRequest(BaseModel):
    username: str


class UpdateAvatarRequest(BaseModel):
    avatar: str


@router.get("/me", response_model=UserProfileResponse)
def get_me(current_user: User = Depends(get_current_user)):
    return UserProfileResponse(
        user_id=current_user.id,
        email=current_user.email,
        username=current_user.username,
        avatar=current_user.avatar,
    )


@router.patch("/me/username", response_model=UserProfileResponse)
def update_username(
    req: UpdateUsernameRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    current_user.username = req.username
    db.commit()
    db.refresh(current_user)
    return UserProfileResponse(
        user_id=current_user.id,
        email=current_user.email,
        username=current_user.username,
        avatar=current_user.avatar,
    )


@router.patch("/me/avatar", response_model=UserProfileResponse)
def update_avatar(
    req: UpdateAvatarRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    current_user.avatar = req.avatar
    db.commit()
    db.refresh(current_user)
    return UserProfileResponse(
        user_id=current_user.id,
        email=current_user.email,
        username=current_user.username,
        avatar=current_user.avatar,
    )
