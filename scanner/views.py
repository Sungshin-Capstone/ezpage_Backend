from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser
from rest_framework import status
from .models import ScanResult
from .serializers import ScanResultSerializer
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.conf import settings

class ReceiptScanView(APIView):
    parser_classes = [MultiPartParser]

    def post(self, request):
        image = request.data.get('image')
        if not image:
            return Response({'error': '이미지가 필요합니다.'}, status=status.HTTP_400_BAD_REQUEST)

        # 임시 저장
        result = ScanResult.objects.create(
            scan_type='receipt',
            image=image,
            extracted_text='',
            extracted_data={},  # 실제 AI 처리 전이므로 빈 값
        )
        # 🔹 여기에 AI 결과가 연동될 자리 (현재는 dummy)
        dummy_result = {
            "items": [
                {"name": "샌드위치", "price": 7.5, "currency": "USD"},
                {"name": "커피", "price": 3.0, "currency": "USD"}
            ],
            "translated": [
                {"name_kr": "샌드위치", "price_kr": 9900},
                {"name_kr": "커피", "price_kr": 3900}
            ],
            "recommend_payment": "현지 화폐 (USD)로 지불 권장",
            "image_preview": result.image.url
        }

        return Response(dummy_result, status=status.HTTP_200_OK)


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