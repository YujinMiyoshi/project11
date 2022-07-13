from django.urls import path
from .views import StoreList, StaffList, StaffCalender, Booking

urlpatterns = [
    path('', StoreList.as_view(), name='store_list'),
    path('store/<int:pk>/staffs/', StaffList.as_view(), name='staff_list'),
    path('staff/<int:pk>/staffs/', StaffCalender.as_view(), name='calendar'),
    path('staff/<int:pk>/calendar/<int:year>/<int:month>/<int:day>/', StaffCalender.as_view(), name='calendar'),
    path('staff/<int:pk>/booking/<int:year>/<int:month>/<int:day>/<int:hour>/', Booking.as_view(), name='booking'),
]