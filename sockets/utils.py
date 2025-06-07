from jose import jwt
from constants import SECRET_KEY, ALGORITHM

def decode_token(token: str):
    payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    user_id: str = payload.get("sub")
    return user_id
