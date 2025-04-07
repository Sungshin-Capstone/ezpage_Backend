from django.shortcuts import render

# Create your views here.
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser
from rest_framework import status
from .models import ScanResult
from .serializers import ScanResultSerializer

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
        serializer = ScanResultSerializer(result)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


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
