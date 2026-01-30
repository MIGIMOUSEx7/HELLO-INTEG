from django.http import HttpResponse # Make sure this import is at the top
from rest_framework import viewsets
from .models import Product, Order
from .serializers import ProductSerializer, OrderSerializer
from .models import User
from .serializers import UserSerializer


# Add this function below your imports
def home(request):
    return HttpResponse("<h1>Welcome to your E-commerce Backend</h1><p>Visit /api/ to see your data.</p>")

class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer

class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer 
    
class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer