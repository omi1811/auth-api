from fastapi import Depends, FastAPI, HTTPException
from fastapi.security import OAuth2PasswordBearer
from src.auth import hash_password, verify_token
from src.schemas import UserCreate, UserResponse, TokenResponse, UserLogin
from src.auth import verify_password, create_access_token, decode_access_token
from pydantic import EmailStr   
from datetime import datetime
import json
from pathlib import Path


app = FastAPI(
    title="Authentication API",
    description="A simple authentication API using FastAPI",
    version="1.0.0",
)

DB_FILE = Path("users_db.json")

def load_users():
    """Load users from JSON file."""
    if DB_FILE.exists():
        with open(DB_FILE, "r") as f:
            return json.load(f)
    return []

def save_users(users):
    """Save users to JSON file."""
    with open(DB_FILE, "w") as f:
        json.dump(users, f, indent=2, default=str)

# Initialize DB file if it doesn't exist
if not DB_FILE.exists():
    save_users([])

@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/register", response_model=UserResponse, status_code=201)
async def register_user(user: UserCreate):
    # Check if user already exists
    for existing_user in load_users():
        if existing_user["email"] == user.email:
            raise HTTPException(status_code=400, detail="User already exists")

    # Hash the password
    hashed_password = hash_password(user.password)

    # Create new user
    new_user = {
        "id": len(load_users()) + 1,
        "email": user.email,
        "hashed_password": hashed_password,
        "created_at": datetime.now()
    }

    # Store the user (in a real application, this would be stored in a database)
    users = load_users()
    users.append(new_user)
    save_users(users)

    return UserResponse(**new_user)

@app.post("/login", response_model=TokenResponse)
async def login_user(login_data: UserLogin):
    email = login_data.email
    password = login_data.password

    users = load_users()    # Find the user
    user = next((u for u in users if u["email"] == email), None)
    if not user:
        raise HTTPException(status_code=400, detail="Invalid credentials")

    # Check the password
    if not verify_password(password, user["hashed_password"]):
        raise HTTPException(status_code=400, detail="Invalid credentials")

    # Generate a token (in a real application, this would be a JWT or similar)
    token_data = {"sub": user["id"], "email": user["email"]}
    access_token = create_access_token(data=token_data)

    return TokenResponse(access_token=access_token, token_type="bearer")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

def get_current_user(token: str = Depends(oauth2_scheme)) -> dict:
    payload = decode_access_token(token)
    if payload is None or "sub" not in payload or "email" not in payload:
        raise HTTPException(status_code=401, detail="Invalid token")

    user_id = payload.get("sub")
    email = payload.get("email")

    # Find the user in the database
    users = load_users()
    user = next((u for u in users if u["id"] == user_id and u["email"] == email), None)
    if user is None:
        raise HTTPException(status_code=401, detail="User not found")

    return user
@app.get("/profile")
async def get_profile(current_user: dict = Depends(get_current_user)):
    return {"email": current_user["email"], "created_at": current_user["created_at"]}