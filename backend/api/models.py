from datetime import timedelta,datetime
from math import ceil
from django.db import models
from django.conf import settings

DEFAULT_HOURLY_RATE = settings.DEFAULT_HOURLY_RATE

class Settings(models.Model):
    hourly_rate = models.DecimalField(max_digits=10, decimal_places=2, default=settings.DEFAULT_HOURLY_RATE)

    def save(self, *args, **kwargs):
        self.pk = self.id = 1
        super().save(*args, **kwargs)

class Brand(models.Model):
    name = models.CharField(max_length=100)
    daily_budget = models.DecimalField(max_digits=10, decimal_places=2)
    monthly_budget = models.DecimalField(max_digits=12, decimal_places=2)
    daily_spend = models.DecimalField(max_digits=10, decimal_places=2, default=0, null=True)
    monthly_spend = models.DecimalField(max_digits=12, decimal_places=2, default=0, null=True)
    last_spend_update = models.DateTimeField(default=None, null=True)

    def get_daily_spend(self):
        ads = self.ads.all().order_by('-start_time')
        spend_list = []

        for ad in ads:
            ad_daily_spends = ad.get_daily_spend()
            for daily_spend in ad_daily_spends:
                date_idx = [date_idx for date_idx, date in enumerate(spend_list) if date['date'] == daily_spend['date']]
                if len(date_idx) > 0:
                    existingDate = date_idx[0]
                    spend_list[existingDate] = {
                        'date': daily_spend['date'],
                        'duration': daily_spend['duration'] + spend_list[existingDate]['duration']
                    }
                else:
                    spend_list.append({
                        'date': daily_spend['date'],
                        'duration': daily_spend['duration']
                    })

        return spend_list
    
    def get_monthly_spend(self):
        ads = self.ads.all().order_by('-start_time')
        spend_list = []

        for ad in ads:
            ad_daily_spends = ad.get_daily_spend()
            for daily_spend in ad_daily_spends:
                date_idx = [date_idx for date_idx, date in enumerate(spend_list) if date['month'] == daily_spend['date'].strftime('%Y-%m')]
                if len(date_idx) > 0:
                    existingDate = date_idx[0]
                    spend_list[existingDate] = {
                        'month': daily_spend['date'].strftime('%Y-%m'),
                        'duration': daily_spend['duration'] + spend_list[existingDate]['duration']
                    }
                else:
                    spend_list.append({
                        'month': daily_spend['date'].strftime('%Y-%m'),
                        'duration': daily_spend['duration']
                    })
        return spend_list


    def get_month_spend(self, month):
        spend_list = self.get_monthly_spend()
        for spend in spend_list:
            if spend['month'] == month:
                return spend['duration']
        return 0

    def get_date_spend(self, date):
        spend_list = self.get_daily_spend()
        for spend in spend_list:
            if spend['date'] == date:
                return spend['duration']
        return 0

    def __str__(self):
        return f"Brand #{self.name}"

class Ad(models.Model):
    active = models.BooleanField(default=False)
    brand = models.ForeignKey(Brand, related_name='ads', on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    last_active_time = models.DateTimeField(default=None, null=True)

    def __str__(self):
        return f"Ad: {self.name} ({self.start_time} - {self.end_time})"
    
    def get_daily_spend(self):

        list = []
        now = datetime.now(tz=self.start_time.tzinfo) if self.start_time.tzinfo else datetime.now()        
        current = self.start_time
        end_time = self.end_time

        if (self.end_time > now):
            end_time = now
        
        while current.date() < end_time.date():
            # End of the current day
            day_end = datetime.combine(current.date(), datetime.max.time(), tzinfo=current.tzinfo)
            duration = day_end - current
            list.append({
                'date': current.date(),
                'duration': ceil(duration.total_seconds() / 3600)
            })
            current = day_end + timedelta(seconds=1)  # Move to start of next day

        # Add final partial day
        duration = end_time - current
        list.append({
            'date': current.date(),
            'duration': ceil(duration.total_seconds() / 3600)
        })

        return list
    

class AdSpend(models.Model):
    ad = models.ForeignKey(Ad, on_delete=models.CASCADE)
    date = models.DateField()
    spent = models.DecimalField(max_digits=10, decimal_places=2)