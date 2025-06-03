from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework import status
from .models import ScanResult
from .serializers import ScanResultSerializer
from rest_framework.views import APIView
from rest_framework.response import Response
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.conf import settings
from rest_framework.permissions import IsAuthenticated

class ReceiptScanView(APIView):
    parser_classes = [MultiPartParser]

    def post(self, request):
        image = request.data.get('image')
        if not image:
            return Response({'error': '이미지가 필요합니다.'}, status=status.HTTP_400_BAD_REQUEST)

        result = ScanResult.objects.create(
            scan_type='receipt',
            image=image,
            extracted_text='',
            extracted_data={},
        )

        # AI팀 서버로 이미지 전송
        ai_server_url = 'http://ai-server/scan'  # 🔴 AI팀 서버 주소로 변경 필요
        files = {'image': (image.name, image, image.content_type)}

        try:
            ai_response = requests.post(ai_server_url, files=files, timeout=10)  # 10초 제한
            ai_response.raise_for_status()  # 오류 있으면 예외 발생
            # AI팀에서 결과(JSON)를 받음
            ai_result = ai_response.json()
            #결과를 DB에 저장
            result.extracted_data = ai_result
            result.save()
            # 프론트에 JSON 결과 응답
            return Response(ai_result, status=status.HTTP_200_OK)

        except requests.RequestException as e:
            return Response({'error': 'AI 서버와 통신 실패', 'details': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class CurrencyScanView(APIView):
    parser_classes = [MultiPartParser]

    def post(self, request):
        image = request.data.get('image')
        if not image:
            return Response({'error': '이미지가 필요합니다.'}, status=status.HTTP_400_BAD_REQUEST)

        result = ScanResult.objects.create(
            scan_type='currency',
            image=image,
            extracted_text='',
            extracted_data={},
        )
        serializer = ScanResultSerializer(result)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

class ImageUploadAPIView(APIView):
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request, *args, **kwargs):
        image = request.FILES.get("image")
        if not image:
            return Response({"error": "No image uploaded."}, status=400)

        file_path = default_storage.save(f"uploads/{image.name}", ContentFile(image.read()))
        image_url = request.build_absolute_uri(settings.MEDIA_URL + file_path.replace("uploads/", ""))

        return Response({
            "message": "Image uploaded successfully",
            "image_url": image_url
        }, status=201)

class WalletScanResultView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser, JSONParser]
    # ...
