from multiprocessing import context
from django.shortcuts import render, get_object_or_404
from django.views.generic import ListView
from .models import Store, Staff

class StoreList(ListView):
    model = Store
    ordering = 'name'
    template_name = 'booking/store_list.html'

class StaffList(ListView):
    model = Staff
    ordering = 'name'
    template_name = 'booking/staff_list.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['store'] = self.store
        return context

    def get_queryset(self):
        store = self.store = get_object_or_404(Store, pk=self.kwargs['pk'])
        queryset = super().get_queryset().filter(store=store)
        return queryset
        
# Create your views here.
