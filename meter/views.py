import csv
import datetime
import operator
import os
from django.http import Http404
from django.shortcuts import render, redirect
from django.views import View

from meter.models import Meter


# Create your views here.

class DataReadHelper:
    def get_ordered_value_key_and_dates_dict_from_existing_csv(self, file_path):
        dates = dict()
        x_axis = list()
        y_axis = list()
        if file_path:
            with open(file_path) as csv_file:
                for row in csv.reader(csv_file):
                    try:
                        date = row[0].split('-')
                        dates[datetime.date(year=int(date[0]), month=int(date[1]), day=int(date[2]))] = float(
                            row[1])
                    except:
                        if row[1].isdigit():
                            dates['null'] = float(row[1])

            sorted_dates = sorted(dates.items(), key=operator.itemgetter(0))
            for i in sorted_dates:
                x_axis.append(('0' if len(str(i[0].day)) < 2 else '') + str(i[0].day) + '/' + (
                    '0' if len(str(i[0].month)) < 2 else '') + str(i[0].month) + '/' + str(i[0].year))
                y_axis.append(dates[i[0]])

        return x_axis, y_axis, dates

    def get_ordered_value_key_and_dates_dict_from_not_existing_csv(self, file_path, file, pk):
        x_axis, y_axis, dates = self.get_ordered_value_key_and_dates_dict_from_existing_csv(file_path)
        try:
            file_path = file.read().decode('utf-8')

            dates_new = dict()
            x_axis_new = list()
            y_axis_new = list()

            for row in file_path.split('\r\n'):
                if row:
                    date, value = row.split(',')
                try:
                    date = date.split('-')
                    dates_new[datetime.date(year=int(date[0]), month=int(date[1]), day=int(date[2]))] = float(value)
                except:
                    if value.isdigit():
                        dates_new['null'] = float(value)

            for key in dates_new:
                dates[key] = dates_new[key]

            sorted_dates = sorted(dates.items(), key=operator.itemgetter(0))
            for i in sorted_dates:
                x_axis_new.append(('0' if len(str(i[0].day)) < 2 else '') + str(i[0].day) + '/' + (
                    '0' if len(str(i[0].month)) < 2 else '') + str(i[0].month) + '/' + str(i[0].year))
                y_axis_new.append(dates[i[0]])

            with open(f"meter_csv/{pk}.csv", 'w', newline='') as csv_file:
                opened = csv.writer(csv_file)
                opened.writerow(['DATE', 'VALUE'])
                for key, value in sorted_dates:
                    opened.writerow([str(key), str(value)])
        except:
            return False
        return True

    def get_x_axis_y_axis_data_from_sorted_dates(self, dates, x_axis, y_axis):
        pass

    def check_file_extention(self, file):
        if str(file.name)[-4:] == '.csv':
            if len(str(file.name)) >= 5:
                return True
        return False


class IndexPage(View):
    def post(self, request):
        if request.POST.get('create_meter_button'):
            try:
                meter_name = request.POST.get('meter_name')
                meter_resource = request.POST.get('meter_resource')
                meter_unit = request.POST.get('meter_unit')
                new_meter = Meter.objects.create(name=meter_name, resource_type=meter_resource, unit=meter_unit)
                success = True
            except:
                success = False
            request.session['success'] = success
        else:
            if os.path.exists(f"meter_csv/{request.POST.get('delete_meter')}.csv"):
                os.remove(f"meter_csv/{request.POST.get('delete_meter')}.csv")
                meter = Meter.objects.get(pk=request.POST.get('delete_meter'))
                meter.meter_csv_file = None
                meter.save()
            meter = Meter.objects.get(pk=request.POST.get('delete_meter'))
            meter.delete()
        return redirect(request.path)

    def get(self, request):
        success = request.session.get('success', None)
        if success in [True, False]:
            del (request.session['success'])

        meters = Meter.objects.all().order_by('pk')
        return render(request, 'meter/index.html', {"meters": meters, "success": success})


class MeterDetails(View, DataReadHelper):
    def post(self, request, pk):
        if request.POST.get('reset_meter'):
            if os.path.exists(f'meter_csv/{pk}.csv'):
                os.remove(f'meter_csv/{pk}.csv')
                meter = Meter.objects.get(pk=pk)
                meter.meter_csv_file = None
                meter.save()
        else:
            file = request.FILES.get('meter_file')
            if self.check_file_extention(file):
                file.name = f"{pk}.csv"
                meter = Meter.objects.get(pk=pk)
                if meter.meter_csv_file:
                    file_path = str(meter.meter_csv_file)
                    self.get_ordered_value_key_and_dates_dict_from_not_existing_csv(file_path=file_path, file=file,
                                                                                    pk=pk)
                else:
                    meter.meter_csv_file = file
                    meter.save()
                    file_path = str(meter.meter_csv_file)

        return redirect(request.path)

    def get(self, request, pk):
        try:
            meter = Meter.objects.get(pk=pk)
            file_path = str(meter.meter_csv_file)

            last_reading_date = None
            last_reading = None
            x_axis = list()
            y_axis = list()

            if file_path:
                x_axis, y_axis, dates = self.get_ordered_value_key_and_dates_dict_from_existing_csv(file_path=file_path)
            try:
                last_reading_date = max(dates)
                last_reading = dates[max(dates)]
            except:
                last_reading = 'null'
                last_reading_date = 'null'
        except Meter.DoesNotExist:
            return Http404
        return render(request, 'meter/meter_details.html',
                      {"meter": meter, 'pk': pk, 'last_reading_date': last_reading_date, 'last_reading': last_reading,
                       'x_axis': x_axis, 'y_axis': y_axis})


class NewMeter(View):
    def get(self, request):
        return render(request, 'meter/new_meter.html', {})
