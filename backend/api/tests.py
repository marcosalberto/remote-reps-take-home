from datetime import datetime, timedelta
from django.test import TestCase
from django.utils import timezone
from freezegun import freeze_time
from .models import AdSpend, Brand, Ad
from .tasks import task_update_adspend, task_ad_scheduler, task_update_brand_spend

class BrandTestCase(TestCase):
    def setUp(self):
        self.brand = Brand.objects.create(
            name="Brand 1", 
            daily_budget=100.00, 
            monthly_budget=200.00
        )

        self.ad1 = Ad.objects.create(
            active=True, 
            brand=self.brand, 
            name="Ad 1", 
            start_time=datetime(2023, 1, 1, 9, 0), 
            end_time=datetime(2023, 1, 1, 17, 0)
        )

        self.ad2 = Ad.objects.create(
            active=True, 
            brand=self.brand, 
            name="Ad 2", 
            start_time=datetime(2023, 1, 1, 9, 0), 
            end_time=datetime(2023, 1, 1, 20, 0)
        )

    def test_brand_create(self):
        self.assertIsNotNone(self.brand)
        self.assertEqual(self.brand.name, "Brand 1")
        self.assertEqual(self.brand.daily_budget, 100.00)
        self.assertEqual(self.brand.monthly_budget, 200.00)

    def test_brand_daily_spend_one_day(self):
        self.assertEqual(self.brand.get_daily_spend(), [
            {
                "date": datetime(2023, 1, 1).date(), 
                "duration": 19
            }
        ])

    def test_brand_daily_spend_many_days(self):
        self.ad1.end_time = datetime(2023, 1, 3, 12, 0)
        self.ad2.end_time = datetime(2023, 1, 3, 8, 0)
        
        self.ad1.save()
        self.ad2.save()

        self.assertEqual(self.brand.get_daily_spend(), [
            {
                "date": datetime(2023, 1, 1).date(), 
                "duration": 30
            }, 
            {
                "date": datetime(2023, 1, 2).date(), 
                "duration": 48
            },
            {
                "date": datetime(2023, 1, 3).date(), 
                "duration": 20
            },
        ])

    def test_brand_monthly_spend_one_day(self):
        self.assertEqual(self.brand.get_monthly_spend(), [
            {
                "month": datetime(2023, 1, 1).strftime('%Y-%m'), 
                "duration": 19
            }
        ])

    def test_brand_monthly_spend_many_days(self):
        self.ad1.end_time = datetime(2023, 1, 3, 12, 0)
        self.ad2.end_time = datetime(2023, 1, 3, 8, 0)
        self.ad1.save()
        self.ad2.save()
        self.assertEqual(self.brand.get_monthly_spend(), [
            {
                "month": datetime(2023, 1, 1).date().strftime('%Y-%m'), 
                "duration": 98
            }
        ])

    def test_brand_monthly_spend_many_months(self):
        self.ad1.end_time = datetime(2023, 2, 3, 9, 0)
        self.ad2.end_time = datetime(2023, 1, 3, 8, 0)
        self.ad1.save()
        self.ad2.save()
        self.assertEqual(self.brand.get_monthly_spend(), [
            {
                "month": datetime(2023, 1, 1).date().strftime('%Y-%m'), 
                "duration": 782
            },
            {
                "month": datetime(2023, 2, 1).date().strftime('%Y-%m'), 
                "duration": 57
            },
        ])

    def test_brand_date_spend(self):
        self.ad1.end_time = datetime(2023, 1, 3, 12, 0)
        self.ad2.end_time = datetime(2023, 1, 3, 8, 0)
        
        self.ad1.save()
        self.ad2.save()

        self.assertEqual(self.brand.get_date_spend(datetime(2023, 1, 1).date()), 30)
        self.assertEqual(self.brand.get_date_spend(datetime(2023, 1, 2).date()), 48)
        self.assertEqual(self.brand.get_date_spend(datetime(2023, 1, 3).date()), 20)

    def test_brand_month_spend(self):
        self.ad1.end_time = datetime(2023, 2, 3, 9, 0)
        self.ad2.end_time = datetime(2023, 1, 3, 8, 0)
        
        self.ad1.save()
        self.ad2.save()

        self.assertEqual(self.brand.get_month_spend('2023-01'), 782)
        self.assertEqual(self.brand.get_month_spend('2023-02'), 57)


class AdTestCase(TestCase):
    def setUp(self):
        self.brand = Brand.objects.create(
            name="Brand 1", 
            daily_budget=100.00, 
            monthly_budget=200.00
        )

        self.ad = Ad.objects.create(
            active=True, 
            brand=self.brand, 
            name="Ad 1", 
            start_time=datetime(2023, 1, 1, 9, 0), 
            end_time=datetime(2023, 1, 1, 17, 0)
        )

    def test_create(self):
        self.assertIsNotNone(self.ad)
        self.assertEqual(self.ad.active, True)
        self.assertEqual(self.ad.brand.name, "Brand 1")
        self.assertEqual(self.ad.name, "Ad 1")
        self.assertEqual(self.ad.start_time, datetime(2023, 1, 1, 9, 0))
        self.assertEqual(self.ad.end_time, datetime(2023, 1, 1, 17, 0))

    def test_ad_spend_with_1_day(self):
        self.assertEqual(self.ad.get_daily_spend(), [{
            "date": datetime(2023, 1, 1).date(), 
            "duration": 8
        }])

    def test_ad_spend_many_days(self):
        self.ad.end_time = datetime(2023, 1, 3, 8, 0)
        self.ad.save()

        self.assertEqual(self.ad.get_daily_spend(), [
            {
                "date": datetime(2023, 1, 1).date(), 
                "duration": 15
            }, 
            {
                "date": datetime(2023, 1, 2).date(), 
                "duration": 24
            },
            {
                "date": datetime(2023, 1, 3).date(), 
                "duration": 8
            },
        ])

    @freeze_time("2023-1-3 12:00:00")
    def test_ad_spend_ending_in_future(self):
        now = datetime.now()
        self.ad.start_time = now - timedelta(hours=2)
        self.ad.end_time = now + timedelta(hours=2)
        self.ad.save()

        self.assertEqual(self.ad.get_daily_spend(), [{
            "date": datetime(2023, 1, 3).date(), 
            "duration": 2
        }])

class TaskAdScheduler(TestCase):
    def setUp(self):
        self.brand = Brand.objects.create(
            name="Brand 1", 
            daily_budget=100.00, 
            monthly_budget=200.00
        )

        self.ad1 = Ad.objects.create(
            active=False, 
            brand=self.brand, 
            name="Ad 1", 
            start_time=datetime(2023, 1, 1, 9, 0), 
            end_time=datetime(2023, 1, 1, 17, 0)
        )
    
    @freeze_time("2023-1-1 10:00:00")
    def test_activate_ad(self):
        task_ad_scheduler()
        
        self.ad1.refresh_from_db()

        self.assertEqual(self.ad1.active, True)


    @freeze_time("2023-1-1 10:00:00")
    def test_activate_budget_exceeded(self):
        self.brand.daily_spend = 120
        self.brand.save()

        task_ad_scheduler()
        
        self.ad1.refresh_from_db()

        self.assertEqual(self.ad1.active, False)
    
    @freeze_time("2023-1-1 18:00:00")
    def test_deactivate_ad(self):
        self.ad1.active = True
        self.ad1.save()

        task_ad_scheduler()

        self.ad1.refresh_from_db()

        self.assertEqual(self.ad1.active, False)

class TaskUpdateAdSpend(TestCase):
    def setUp(self):
        self.brand = Brand.objects.create(
            name="Brand 1", 
            daily_budget=100.00, 
            monthly_budget=200.00
        )

        self.ad1 = Ad.objects.create(
            active=False, 
            brand=self.brand, 
            name="Ad 1", 
            start_time=datetime(2023, 1, 1, 9, 0), 
            end_time=datetime(2023, 1, 2, 17, 0)
        )
    
    @freeze_time("2023-1-1 12:00:00", as_kwarg='frozen_time')
    def test_spend_one_day(self, frozen_time):
        task_ad_scheduler()
        
        frozen_time.move_to("2023-1-1 14:00:00")
        task_update_adspend()
        
        spend = AdSpend.objects.get(ad=self.ad1, date=datetime(2023, 1, 1))
        self.assertEqual(spend.spent, 2)
    
    @freeze_time("2023-1-1 12:00:00", as_kwarg='frozen_time')
    def test_spend_many_days(self, frozen_time):
        task_ad_scheduler()
        
        frozen_time.move_to("2023-1-2 14:00:00")
        task_update_adspend()
        
        spend = AdSpend.objects.get(ad=self.ad1, date=datetime(2023, 1, 2))
        self.assertEqual(spend.spent, 14)

class TaskUpgradeBrandSpend(TestCase):
    def setUp(self):
        self.brand = Brand.objects.create(
            name="Brand 1", 
            daily_budget=100.00, 
            monthly_budget=200.00,
            daily_spend=0.00,
            monthly_spend=0.00,
            last_spend_update=timezone.now().date() - timedelta(days=1)
        )

        self.ad1 = Ad.objects.create(
            active=False, 
            brand=self.brand, 
            name="Ad 1", 
            start_time=datetime(2023, 1, 1, 9, 0), 
            end_time=datetime(2023, 1, 2, 17, 0)
        )
    
    @freeze_time("2023-1-1 12:00:00", as_kwarg='frozen_time')
    def test_spend_one_day(self, frozen_time):
        task_ad_scheduler()
        
        frozen_time.move_to("2023-1-1 14:00:00")
        task_update_adspend()
        task_update_brand_spend()

        frozen_time.move_to("2023-1-1 16:00:00")
        task_update_adspend()
        task_update_brand_spend()
        
        self.brand.refresh_from_db()
        
        self.assertEqual(self.brand.daily_spend, 4)
        self.assertEqual(self.brand.monthly_spend, 4)
    
    @freeze_time("2023-1-1 12:00:00", as_kwarg='frozen_time')
    def test_spend_many_days(self, frozen_time):
        task_ad_scheduler()

        frozen_time.move_to("2023-1-1 14:00:00")
        task_update_adspend()
        task_update_brand_spend()
        
        frozen_time.move_to("2023-1-1 16:00:00")
        task_update_adspend()
        task_update_brand_spend()

        frozen_time.move_to("2023-1-2 14:00:00")
        task_update_adspend()
        task_update_brand_spend()
        
        self.brand.refresh_from_db()
        
        self.assertEqual(self.brand.daily_spend, 14)
        self.assertEqual(self.brand.monthly_spend, 18)

        frozen_time.move_to("2023-2-1 10:00:00")
        task_update_adspend()
        task_update_brand_spend()

        self.brand.refresh_from_db()
        self.assertEqual(self.brand.daily_spend, 10)
        self.assertEqual(self.brand.monthly_spend, 10)