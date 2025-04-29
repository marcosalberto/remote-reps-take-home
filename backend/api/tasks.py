import logging
from datetime import datetime
from math import ceil
from celery import shared_task
from django.utils import timezone
from .models import Brand, Ad, AdSpend, Settings
from django.db.models import Sum

logger = logging.getLogger(__name__)

@shared_task
def task_ad_scheduler():
    now = timezone.now()
    ads = Ad.objects.exclude(start_time=None).exclude(end_time=None)

    for ad in ads:
        adLastState = ad.active
        
        if ad.start_time <= now <= ad.end_time:
            if ad.brand.monthly_budget > ad.brand.monthly_spend and ad.brand.daily_budget > ad.brand.daily_spend:
                ad.active = True
            
                if not adLastState:
                    ad.last_active_time = datetime.now()
                    logging.info(f"Ad {ad.id} activated.")
            else:
                print(f"Ad {ad.id} not activated due budget exceeded.")
        else:
            ad.active = False
            if adLastState:
                logging.info(f"Ad {ad.id} has been deactivated.")
        
        ad.save()

@shared_task
def task_update_adspend():
    now = timezone.now()
    today = now.replace(hour=0, minute=0, second=0, microsecond=0)
    active_ads = Ad.objects.filter(active=True)
    
    for active_ad in active_ads:
        start_time = today
        end_time = now

        if (active_ad.last_active_time > today):
            start_time = active_ad.last_active_time        

        spend = end_time - start_time
        AdSpend.objects.update_or_create(ad=active_ad, date=today.date(), defaults={'spent': ceil(spend.total_seconds() / 3600)})


@shared_task
def task_update_brand_spend():

    current_day = timezone.now()
    
    for brand in Brand.objects.all():
        if (brand.last_spend_update != current_day):
            brand.daily_spend = 0
            if (brand.last_spend_update and brand.last_spend_update.month != current_day.month):
                brand.monthly_spend = 0
            brand.last_spend_update = current_day
            brand.save()

        current_day_spend = AdSpend.objects.filter(ad__brand=brand, date=current_day.date()).aggregate(Sum('spent'))['spent__sum']
        current_month_spend = AdSpend.objects.filter(ad__brand=brand, date__month=current_day.month, date__year=current_day.year).aggregate(Sum('spent'))['spent__sum']
    
        brand.daily_spend = current_day_spend
        brand.monthly_spend = current_month_spend
        brand.last_spend_update = current_day
        brand.save()

        if brand.monthly_budget <= brand.monthly_spend or brand.daily_budget <= brand.daily_spend:
            brand.ads.filter(active=True).update(active=False)