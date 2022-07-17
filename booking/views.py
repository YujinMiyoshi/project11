from django.conf import settings
import datetime
from django.utils import timezone
from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, TemplateView, CreateView, UpdateView, DeleteView
from .models import Schedule, Store, Staff
from django.db.models import Q
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth import get_user_model, login, authenticate
from django.urls import reverse_lazy
from django.core.exceptions import PermissionDenied
from django.views.decorators.http import require_POST
from django.contrib.auth.forms import UserCreationForm

User = get_user_model()

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
        start = datetime.datetime(year=year, month=month, day=day, hour=hour)
        end = datetime.datetime(year=year, month=month, day=day, hour=hour + 1)
        if Schedule.objects.filter(staff=staff, start=start).exists():
            messages.error(self.request, 'すみません、入れ違いで予約がありました。別の日はどうですか？')
        else:
            schedule = form.save(commit=False)
            schedule.staff = staff
            schedule.start = start
            schedule.end = end
            schedule.save()
        return redirect('calendar', pk=staff.pk, year=year, month=month, day=day)

class MyPage(LoginRequiredMixin, TemplateView):
    template_name = 'booking/my_page.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['staff_list'] = Staff.objects.filter(user=self.request.user).order_by('name')
        context['schedule_list'] = Schedule.objects.filter(staff__user=self.request.user, start__gte=timezone.now()).order_by('name')
        return context

class OnlyUserMixin(UserPassesTestMixin):
    raise_exception = True

    def test_func(self):
        return self.kwargs['pk'] == self.request.user.pk or self.request.user.is_superuser

class MyPageWithPk(OnlyUserMixin, TemplateView):
    template_name = 'booking/my_page.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['user'] = get_object_or_404(User, pk=self.kwargs['pk'])
        context['staff_list'] = Staff.objects.filter(user__pk=self.kwargs['pk']).order_by('name')
        context['schedule_list'] = Schedule.objects.filter(staff__user__pk=self.kwargs['pk'], start__gte=timezone.now()).order_by('name')
        return context

class OnlyStaffMixin(UserPassesTestMixin):
    raise_exception = True

    def test_func(self):
        staff = get_object_or_404(Staff, pk=self.kwargs['pk'])
        return staff.user == self.request.user or self.request.user.is_superuser

class MyPageCalendar(OnlyStaffMixin, StaffCalender):
    template_name = 'booking/my_page_calendar.html'

class MyPageDetail(OnlyStaffMixin,TemplateView):
    template_name = 'booking/my_page_day_detail.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        pk = self.kwargs['pk']
        staff = get_object_or_404(Staff, pk=pk)
        year = self.kwargs.get('year')
        month = self.kwargs.get('month')
        day = self.kwargs.get('day')
        date = datetime.date(year=year, month=month, day=day)

        calendar = {}
        for hour in range(9, 18):
            calendar[hour] = []

        start_time = datetime.datetime.combine(date, datetime.time(hour=9, minute=0, second=0))
        end_time = datetime.datetime.combine(date, datetime.time(hour=17, minute=0, second=0))
        for schedule in Schedule.objects.filter(staff=staff).exclude(Q(start__gt=end_time) | Q(end__lt=start_time)):
            local_dt = timezone.localtime(schedule.start)
            booking_date = local_dt.date()
            booking_hour = local_dt.hour
            if booking_hour in calendar:
                calendar[booking_hour].append(schedule)

        context['calendar'] = calendar
        context['staff'] = staff
        return context

class OnlyScheduleMixin(UserPassesTestMixin):
    raise_exception = True

    def test_func(self):
        schedule = get_object_or_404(Schedule, pk=self.kwargs['pk'])
        return schedule.staff.user == self.request.user or self.request.user.is_superuser

class MyPageSchedule(OnlyScheduleMixin, UpdateView):
    model = Schedule
    fields = ('start', 'end', 'name')
    success_url = reverse_lazy('my_page')

class MyPageScheduleDelete(OnlyScheduleMixin, DeleteView):
    model = Schedule
    success_url = reverse_lazy('my_page')

@require_POST
def my_page_holiday_add(request, pk, year, month, day, hour):
    staff = get_object_or_404(Staff, pk=pk)
    if staff.user == request.user or request.user.is_superuser:
        start = datetime.datetime(year=year, month=month, day=day, hour=hour)
        end = datetime.datetime(year=year, month=month, day=day, hour=hour + 1)
        Schedule.objects.create(staff=staff, start=start, end=end, name='休暇(システムによる追加)')
        return redirect('my_page_day_detail', pk=pk, year=year, month=month, day=day)

    raise PermissionDenied

class SignUp(CreateView):
    template_name = 'booking/signup.html'
    form_class = UserCreationForm
    success_url = reverse_lazy('signedup')

    def form_valid(self, form):
        response = super().form_valid(form)
        username = form.cleaned_data.get("username")
        password = form.cleaned_data.get("password1")
        user = authenticate(username=username, password=password)
        login(self.request, user)
        return response

class SignedUp(TemplateView):
    template_name = 'booking/signedup.html'

class AddStaff(OnlyUserMixin, CreateView):
    model = Staff
    fields = ('name', 'store')
    success_url = reverse_lazy('my_page')

    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)

class AddStoreError(TemplateView):
    template_name = 'booking/addstore_error.html'

class AddStaffStore(OnlyUserMixin, CreateView):
    model = Staff
    fields = ('name', 'store')
    success_url = reverse_lazy('my_page')

    def form_valid(self, form):
        try:
            form.instance.user = self.request.user
            return super().form_valid(form)
        except:
            return redirect('addstore_error')

class StaffChange(OnlyUserMixin, TemplateView):
    model = Staff
    template_name = 'booking/staff_change.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['staff_list'] = Staff.objects.filter(user = self.request.user)
        return context

class StaffDelete(OnlyStaffMixin, DeleteView):
    model = Staff
    template_name = 'booking/staff_delete.html'

    def get_success_url(self):
        return reverse_lazy("staff_change", kwargs={"pk": self.request.user.pk})

# Create your views here.
