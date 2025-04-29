# Remote Reps Take Home (Python)

This is a API using **Django** for manage ads from an Agency.

## Data Structure Overview

- Brands
- Each brand has:
    - Many Ads
    - Daily Budget in hours
    - Monthly Budget in hours
    - Daily Spend in hours
    - Monthly Spend in hours
    - Last Update
- Ads
    - Many Daily Spend in hours
    - Active
    - Start Time
    - End Time
- Ad Spend
    - Date
    - Spent


### Pseudo-code


    For each Brand:  

        If today is a new day since last update:  
            Reset brand.daily_spend to 0

        If current month != last update month:
            Reset brand.monthly_spend to 0

        Update brand.last_spend_update = now

        For each ad in this brand:
            If ad.start_time is higher than now and ad.end_time is lower than now:
                If brand.has_budget:
                    Update ad.active = True
            Else:
                Update ad.active = False

        # Recalculate total brand spend
        brand.daily_spend = sum of all today's AdSpend for brand
        brand.monthly_spend = sum of all this month's AdSpend for brand

        Save brand state

        If brand.daily_spend >= daily_budget or brand.monthly_spend >= monthly_budget:
            Deactivate all ads for this brand

    Periodic Tasks:

    - Update ad spend every 15 minutes
    - Update brand spend every 15 minutes

## Project Structure

project-root/   
├── backend/ # Django API   
│ ├── admanager/ # Django project directory   
│ ├────── asgi.py # ASGI entry point  
│ ├────── celery.py # Celery configuration  
│ ├────── settings.py # Django settings  
│ ├────── urls.py # URL configuration  
│ └────── wsgi.py # WSGI entry point  
├──── api/ # API directory   
│ ├────── migrations/ # Database migrations  
│ ├────── admin.py # Django admin interface   
│ ├────── apps.py # Django apps   
│ ├────── models.py # Database models  
│ ├────── serializers.py # Data serialization   
│ ├────── tasks.py # Celery tasks  
│ ├────── tests.py # Automated tests   
│ └────── viewsets.py # Django viewsets  
├──── Dockerfile # Dockerfile for build  
├──── manage.py # Django management commands  
├──── requirements.txt # Python dependencies file  
├── README.md #   git 
└── docker-compose.yml # Docker Compose to orchestrate start up  

## Requirements

- Docker
- Docker Compose

## Project Setup

1. Clone this repository

```bash
git clone https://github.com/omarcosalberto/remote-reps-take-home.git
```

2. Enter the project directory

```bash
cd remote-reps-take-home
```

3. Copy `env-example` to `.env` (optional)

```bash
cp env-example .env
```

4. Run project

```bash
docker compose up
```

5. Run tests

```bash
docker compose exec backend python manage.py test
```