from typing import Any
from django.http import HttpRequest
from ninja import NinjaAPI, Schema
from django.contrib.auth.models import User
from django.contrib.auth.hashers import make_password
from ninja.security import HttpBearer
from jwt import encode, decode as jwt_decode, exceptions
from django.conf import settings
from pydantic import BaseModel
from .models import *
from django.shortcuts import get_object_or_404
from datetime import datetime, timedelta

api = NinjaAPI()

class AuthBearer(HttpBearer):
    def authenticate(self, request, token):
        # Cek apakah token ada di daftar hitam
        if BlacklistedToken.objects.filter(token=token).exists():
            return None
        
        try:
            decoded_data = jwt_decode(token, settings.SECRET_KEY, algorithms=['HS256'])

            return User.objects.get(id=decoded_data['user_id'])
        except (exceptions.DecodeError, User.DoesNotExist):
            return None

auth = AuthBearer()

class RegisterSchema(BaseModel):
    username: str
    email: str
    password: str

@api.post("/register")
def register(request, data: RegisterSchema):
    if User.objects.filter(username=data.username).exists():
        return {"error": "Username already taken"}
    
    if User.objects.filter(email=data.email).exists():
        return {"error": "Email already in use"}
    
    user = User(
        username=data.username,
        email=data.email,
        password=make_password(data.password),
    )

    user.save()

    return {"username": user.username, "email": user.email}

class LoginSchema(Schema):
    username: str
    password: str
    
@api.post("/login")
def login(request, payload: LoginSchema):
    try:
        username = payload.username
        password = payload.password

        user = User.objects.get(username=username)

        if not user.check_password(password):
            return {"error": "Password Salah"}
        
        # Set expiration time (1 hour from now)
        expiration = datetime.utcnow() + timedelta(hours=1)
        token = encode({
            'user_id': user.id,
            'exp': expiration
        }, settings.SECRET_KEY, algorithm='HS256')

        return {"username": user.username, "email": user.email, "token": token}
    except User.DoesNotExist:
        return {"error": "Password Atau Username Salah"}

@api.post("/logout", auth=auth)
def logout(request):
    token = request.headers.get("Authorization").split(" ")[1]
    BlacklistedToken.objects.create(token=token)
    return {"message": "Successfully logged out"}

@api.get("/protected", auth=auth)
def protected(request):
    return {"message": "This is a protected endpoint"}

# Definisi Class
class GenreSchema(Schema):
    name: str

# Create
@api.post("/genres", auth=auth)
def create_genre(request, data: GenreSchema):
    # auth.authenticate(request, token) tidak diperlukan jika auth digunakan di decorator

    # Jika autentikasi berhasil, endpoint akan dieksekusi, dan token sudah diverifikasi oleh HttpBearer
    genre = Genre.objects.create(name=data.name)
    return {"id": genre.id, "name": genre.name}

# GET
@api.get("/genres", auth=auth)
def list_genres(request):
    genres = Genre.objects.all()

    return [{"id": genre.id, "name": genre.name} for genre in genres]

# Get By ID
@api.get("/genres/{genre_id}", auth=auth)
def get_genre(request, genre_id: int):
    genre = get_object_or_404(Genre, id=genre_id)
    
    return {"id": genre.id, "name": genre.name}

# Update
@api.put("/genres/{genre_id}", auth=auth)
def update_genre(request, genre_id: int, data: GenreSchema):
    # auth.authenticate(request, token)
    
    genre = get_object_or_404(Genre, id=genre_id)
    genre.name = data.name
    genre.save()
    
    return {"id": genre.id, "name": genre.name}

# Delete
@api.delete("/genres/{genre_id}", auth=auth)
def delete_genre(request, genre_id: int):
    # auth.authenticate(request, token)
    
    genre = get_object_or_404(Genre, id=genre_id)
    genre.delete()
    
    return {"message": "Genre deleted successfully"}
