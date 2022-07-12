from django.urls import path
from .views import StoreList, StaffList

urlpatterns = [
    path('', StoreList.as_view(), name='store_list'),
    path('store/<int:pk>/staffs/', StaffList.as_view(), name='staff_list'),
]