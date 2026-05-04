from database import get_all_tasks
import json

def get_dashboard_data():
    """Fetches dashboard data, ordering by urgency + oldest to newest date"""
    all_tasks = get_all_tasks()

    for task in all_tasks:
        if isinstance(task['entities'], str):
            task['entities'] = json.loads(task['entities'])

    low_urgency_tasks = []
    medium_urgency_tasks = []
    high_urgency_tasks = []

    for task in all_tasks:
        if task['entities']['urgency'] == 'low': 
            low_urgency_tasks.append(task)
        elif task['entities']['urgency'] == 'medium': 
            medium_urgency_tasks.append(task)
        elif task['entities']['urgency'] == 'high': 
            high_urgency_tasks.append(task)
    
    
    low_urgency_tasks = sorted(low_urgency_tasks, key=lambda x: x['created_at'])
    medium_urgency_tasks = sorted(medium_urgency_tasks, key=lambda x: x['created_at'])
    high_urgency_tasks = sorted(high_urgency_tasks, key=lambda x: x['created_at'])

    sorted_tasks = (high_urgency_tasks + medium_urgency_tasks + low_urgency_tasks)

    return sorted_tasks