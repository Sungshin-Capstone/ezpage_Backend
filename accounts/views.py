from django.shortcuts import render
from rest_framework_simplejwt.views import TokenObtainPairView
from .serializers import CustomTokenObtainPairSerializer
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError, InvalidToken
from rest_framework import generics
from .serializers import RegisterSerializer
from django.contrib.auth import get_user_model

User = get_user_model()

class CustomLoginView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer

class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            refresh_token = request.data["refresh"]  # ← 프론트나 Postman에서 refresh 토큰 보내야 함
            token = RefreshToken(refresh_token)
            token.blacklist()  # ← 진짜로 블랙리스트 등록!
            return Response({"message": "로그아웃 되었습니다."}, status=200)
        except (KeyError, TokenError, InvalidToken):
            return Response({"error": "유효하지 않은 refresh token입니다."}, status=400)

class ProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        return Response({
            "user_id": user.id,
            "username": user.username,
            "email": user.email,
            "nickname": user.nickname,
            "name": user.name,
            "country": user.country,
            "profile_image": user.profile_image.url if user.profile_image else None
        })

class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = RegisterSerializer
