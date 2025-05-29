 # tasks.py
from celery import shared_task
from .models import Reward

@shared_task
def add_reward(user_id, points):
    reward = Reward.objects.get(user_id=user_id)
    reward.add_points(points)