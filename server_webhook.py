# Código tomado de https://fastapi.tiangolo.com/tutorial/security/oauth2-jwt/

from datetime import datetime, timedelta, timezone
from typing import Annotated

import jwt
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jwt.exceptions import InvalidTokenError
from passlib.context import CryptContext
from pydantic import BaseModel, Field

import uvicorn

# to get a string like this run:
# openssl rand -hex 32
SECRET_KEY = "09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30


fake_users_db = {
    "johndoe": {
        "username": "johndoe",
        "full_name": "John Doe",
        "email": "johndoe@example.com",
        "hashed_password": "$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW",
        "disabled": False,
    }
}


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: str | None = None


class User(BaseModel):
    username: str
    email: str | None = None
    full_name: str | None = None
    disabled: bool | None = None


class UserInDB(User):
    hashed_password: str


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

app = FastAPI()


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password):
    return pwd_context.hash(password)


def get_user(db, username: str):
    if username in db:
        user_dict = db[username]
        return UserInDB(**user_dict)


def authenticate_user(fake_db, username: str, password: str):
    user = get_user(fake_db, username)
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user


def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except InvalidTokenError:
        raise credentials_exception
    user = get_user(fake_users_db, username=token_data.username)
    if user is None:
        raise credentials_exception
    return user


async def get_current_active_user(
    current_user: Annotated[User, Depends(get_current_user)],
):
    if current_user.disabled:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


@app.post("/token")
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
) -> Token:
    user = authenticate_user(fake_users_db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return Token(access_token=access_token, token_type="bearer")


@app.get("/users/me/", response_model=User)
async def read_users_me(
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    return current_user


@app.get("/users/me/items/")
async def read_own_items(
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    return [{"item_id": "Foo", "owner": current_user.username}]


# -------------------------------------------------------------------------------
# -------------------------------------------------------------------------------
# Código que gestional el webhook de SCAIZEN
# -------------------------------------------------------------------------------
# Esquema para el mensaje que recibirá el endpoint
class OrdenFinalizada(BaseModel):
    timestamp: datetime = Field(
        ...,
        title="Fecha y hora del mensaje. Formato: YYYY-MM-DD HH:MM:SS",
        description="Fecha y hora del mensaje. Formato: YYYY-MM-DD HH:MM:SS",
    )
    serie: int = Field(
        ...,
        title="Número de serie de la orden de SCAIZEN",
        description="Número de serie de la orden de SCAIZEN",
    )
    id_orden: int = Field(
        ...,
        title="ID de la orden SCAIZEN",
        description="ID de la orden SCAIZEN",
    )
    # los posibles valores de tipo son: "carga", "descarga" o "reingreso"
    tipo: str = Field(
        ...,
        title="Tipo de operación",
        description="Tipo de operación, puede ser: 'carga', 'descarga' o 'reingreso'",
    )
    producto: str = Field(
        ...,
        title="Producto",
        description="Producto, puede ser: 'magna', 'diesel' o 'premium'",
    )
    volumen_natural: float = Field(
        ...,
        title="Volumen natural",
        description="Volumen natural del producto",
    )
    volumen_neto: float = Field(
        ...,
        title="Volumen neto",
        description="Volumen neto del producto",
    )
    densidad: float = Field(
        ...,
        title="Densidad",
        description="Densidad del producto",
    )
    temperatura: float = Field(
        ...,
        title="Temperatura",
        description="Temperatura del producto",
    )
    fecha_inicio: datetime = Field(
        ...,
        title="Fecha de inicio",
        description="Fecha de inicio de la operación. Formato: YYYY-MM-DD HH:MM:SS",
    )
    fecha_fin: datetime = Field(
        ...,
        title="Fecha de fin",
        description="Fecha de fin de la operación. Formato: YYYY-MM-DD HH:MM:SS",
    )


# -------------------------------------------------------------------------------
# Endpoint para recibir el mensaje de SCAIZEN
# Funcionamiento:
# - Recibe un mensaje en formato JSON
# - Verifica si el id_orden es par o impar
# - Si es par, devuelve un mensaje de éxito
# - Si es impar, devuelve un mensaje de error
# -------------------------------------------------------------------------------
@app.post("/webhook_scaizen_finalizacion_orden")
async def scaizen_finalizacion_orden_webhook(
    data: OrdenFinalizada,
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    print(f"---------------------------------------------------------")
    print(f"---------------------------------------------------------")
    print(f"Mensaje recibido:")
    print(f"---------------------------------------------------------")
    print(f"{data}")
    print(f"---------------------------------------------------------")
    print(f"---------------------------------------------------------")

    # Verifica si el id_orden es par o impar
    if data.id_orden % 2 == 0:
        retorn = {"status": "success", "message": "Orden procesada con éxito."}
        print(f"-----RESPUESTA OK-----")
        print(f"Orden {data.id_orden} procesada con éxito.")
        print(f"---------------------------------------------------------")
        return retorn
    else:
        print(f"-----RESPUESTA ERROR-----")
        print(f"Orden {data.id_orden} no se puede procesar.")
        print(f"---------------------------------------------------------")
        raise HTTPException(
            status_code=400, detail="ID de orden impar. No se puede procesar."
        )


# home implementation
@app.get("/")
async def home():
    return {
        "message": "Bienvenido, la documentación de la API se encuentra en /docs: http://127.0.0.1:8787/docs"
    }


if __name__ == "__main__":
    uvicorn.run(app, host="localhost", port=8787)
