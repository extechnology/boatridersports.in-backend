from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .ui_serializers import *
from .ui_models import *    


class HomeSliderVideoView(APIView):
    def get(self,request):
        home_slider = HomeSliderVideoModel.objects.first()
        serializer = HomeSliderVideoSerializer(home_slider, context={'request': request})
        return Response(serializer.data)