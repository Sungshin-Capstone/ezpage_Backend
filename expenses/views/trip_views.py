from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from ..models import Trip
from ..serializers import TripSerializer

class TripListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # 로그인한 사용자의 모든 여행 목록 반환
        trips = Trip.objects.filter(user=request.user)
        serializer = TripSerializer(trips, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

class TripCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = TripSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(user=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class TripDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        try:
            trip = Trip.objects.get(pk=pk, user=request.user)
            serializer = TripSerializer(trip)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Trip.DoesNotExist:
            return Response({"error": "여행을 찾을 수 없습니다."}, status=status.HTTP_404_NOT_FOUND)

    def patch(self, request, pk):
        try:
            trip = Trip.objects.get(pk=pk, user=request.user)
            serializer = TripSerializer(trip, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_200_OK)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Trip.DoesNotExist:
            return Response({"error": "여행을 찾을 수 없습니다."}, status=status.HTTP_404_NOT_FOUND)

    def delete(self, request, pk):
        try:
            trip = Trip.objects.get(pk=pk, user=request.user)
            trip.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Trip.DoesNotExist:
            return Response({"error": "여행을 찾을 수 없습니다."}, status=status.HTTP_404_NOT_FOUND)
