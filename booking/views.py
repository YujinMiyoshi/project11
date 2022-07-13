from django.conf import settings
import datetime
from django.utils import timezone
from django.shortcuts import render, get_object_or_404
from django.views.generic import ListView, TemplateView, CreateView
from .models import Schedule, Store, Staff
from django.db.models import Q
from django.contrib import messages, redirects

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

class StaffCalender(TemplateView):
    template_name = 'booking/calendar.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        staff = get_object_or_404(Staff, pk=self.kwargs['pk'])
        today = datetime.date.today()

        year = self.kwargs.get('year')
        month = self.kwargs.get('month')
        day = self.kwargs.get('day')
        if year and month and day:
            base_date = datetime.date(year=year, month=month, day=day)
        else:
            base_date = today

        days = [base_date + datetime.timedelta(days=day) for day in range(7)]
        start_day = days[0]
        end_day = days[-1]

        calendar = {}
        for hour in range(9, 18):
            row = {}
            for day in days:
                row[day] = True
            calendar[hour] = row

        start_time = datetime.datetime.combine(start_day, datetime.time(hour=9, minute=0, second=0))
        end_time = datetime.datetime.combine(end_day, datetime.time(hour=17, minute=0, second=0))
        for schedule in Schedule.objects.filter(staff=staff).exclude(Q(start__gt=end_time) | Q(end__lt=start_time)):
            local_dt = timezone.localtime(schedule.start)
            booking_date = local_dt.date()
            booking_hour = local_dt.hour
            if booking_hour in calendar and booking_date in calendar[booking_hour]:
                calendar[booking_hour][booking_date] = False

        context['staff'] = staff
        context['calendar'] = calendar
        context['days'] = days
        context['start_day'] = start_day
        context['end_day'] = end_day
        context['before'] = days[0] - datetime.timedelta(days=7)
        context['next'] = days[-1] + datetime.timedelta(days=1)
        context['today'] = today
        context['public_holidays'] = settings.PUBLIC_HOLIDAYS

        return context

class Booking(CreateView):
    model = Schedule
    fields = ('name',)
    template_name = 'booking/booking.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['staff'] = get_object_or_404(Staff, pk=self.kwargs['pk'])
        return context

    def form_valid(self, form):
        staff = get_object_or_404(Staff, pk=self.kwargs['pk'])
        year = self.kwargs.get('year')
        month = self.kwargs.get('month')
        day = self.kwargs.get('day')
        hour = self.kwargs.get('hour')
        start = datetime.datetime(year=year, month=month, hour=hour)
        end = datetime.datetime(year=year, month=month, day=day, hour=hour + 1)
        if Schedule.objects.filter(staff=staff, start=start).exists():
            messages.error(self.request, 'すみません、入れ違いで予約がありました。別の日はどうですか？')
        else:
            schedule = form.save(commit=False)
            schedule.staff = staff
            schedule.start = start
            schedule.end = end
            schedule.save()
        return redirects('calendar', pk=staff.pk, year=year, month=month, day=day)

# Create your views here.
