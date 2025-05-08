import os
from dotenv import load_dotenv
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt

load_dotenv()  # Load environment variables from .env file

http_bearer = HTTPBearer()

async def validate_jwt(token: HTTPAuthorizationCredentials = Depends(http_bearer)):
    try:
        payload = jwt.decode(token.credentials, os.getenv("SECRET_KEY"), algorithms=[os.getenv("ALGORITHM")])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")