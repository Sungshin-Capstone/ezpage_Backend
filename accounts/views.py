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
from django.conf import settings

User = get_user_model()

class CustomLoginView(TokenObtainPairView):
    def get(self, request, *args, **kwargs):
        return Response({"detail": "이 API는 POST 요청만 지원합니다."}, status=status.HTTP_405_METHOD_NOT_ALLOWED)

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

from rest_framework.permissions import AllowAny

class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]

class PasswordResetRequestView(APIView):
    def post(self, request):
        email = request.data.get("email")
        if not email:
            return Response({"error": "이메일을 입력하세요."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({"message": "해당 이메일로 가입된 계정이 없습니다."}, status=status.HTTP_404_NOT_FOUND)

        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = token_generator.make_token(user)
        reset_link = f"http://localhost:3000/reset-password-confirm/{uid}/{token}/"  # 프론트 도메인에 맞게 수정

        send_mail(
            subject="[Ezpage] 비밀번호 재설정 링크",
            message=f"다음 링크를 클릭하여 비밀번호를 재설정하세요:\n{reset_link}",
            from_email="eunjun6570@gmail.com",
            recipient_list=[email],
        )

        return Response({"message": "비밀번호 재설정 링크가 이메일로 전송되었습니다."}, status=status.HTTP_200_OK)

from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.contrib.auth import get_user_model
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.core.mail import send_mail

User = get_user_model()
token_generator = PasswordResetTokenGenerator()
class PasswordResetConfirmView(APIView):
    def post(self, request):
        uidb64 = request.data.get("uid")
        token = request.data.get("token")
        new_password = request.data.get("new_password")

        if not (uidb64 and token and new_password):
            return Response({"error": "모든 필드가 필요합니다."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=uid)
        except (User.DoesNotExist, ValueError, TypeError, OverflowError):
            return Response({"error": "유효하지 않은 링크입니다."}, status=status.HTTP_400_BAD_REQUEST)

        if not token_generator.check_token(user, token):
            return Response({"error": "토큰이 유효하지 않거나 만료되었습니다."}, status=status.HTTP_400_BAD_REQUEST)

        user.set_password(new_password)
        user.save()
        return Response({"message": "비밀번호가 성공적으로 재설정되었습니다."}, status=status.HTTP_200_OK)



class LanguageSettingView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        language = request.data.get('language')
        if language not in ['ko', 'en']:
            return Response({"error": "지원되지 않는 언어입니다."}, status=400)

        user = request.user
        user.language = language
        user.save()
        return Response({"message": f"언어가 '{language}'로 변경되었습니다."}, status=200)

class AccountDeleteView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request):
        user = request.user
        try:
            # Delete user's refresh tokens from blacklist
            refresh_token = request.data.get("refresh")
            if refresh_token:
                token = RefreshToken(refresh_token)
                token.blacklist()
            
            # Delete the user account
            user.delete()
            return Response(
                {"message": "계정이 성공적으로 삭제되었습니다."}, 
                status=status.HTTP_200_OK
            )
        except Exception as e:
            return Response(
                {"error": "계정 삭제 중 오류가 발생했습니다."}, 
                status=status.HTTP_400_BAD_REQUEST
            )
from django.http import HttpResponse
from django.core.management import call_command

def run_migrations(request):
    try:
        call_command('migrate')
        return HttpResponse("✅ Migration completed successfully.")
    except Exception as e:
        return HttpResponse(f"❌ Migration failed: {str(e)}", status=500)
