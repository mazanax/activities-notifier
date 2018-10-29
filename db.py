from datetime import datetime
from math import ceil

temp_activities = {}
running_activities = {}


def get_running_activities(user_id):
    global running_activities

    def calculate_progress(started_at, target_time, **_):
        return ceil((datetime.utcnow() - started_at).seconds / target_time * 100)

    if not running_activities.get(user_id):
        running_activities[user_id] = []

    return [{**x, 'progress': calculate_progress(**x)} for x in
            running_activities.get(user_id) if x['started_at'] < datetime.utcnow()]


def has_running_activity(user_id, activity_id):
    return activity_id in [x['id'] for x in get_running_activities(user_id)]


def start_activity(user_id, activity_id):
    global running_activities

    def convert_unit_to_seconds(unit):
        if unit == 'MINUTES':
            return 60
        elif unit == 'HOURS':
            return 3600
        elif unit == 'DAYS':
            return 86400
        else:
            raise RuntimeError('Unknown unit {}'.format(unit))

    if activity_id in [x['id'] for x in get_running_activities(user_id)]:
        return

    activity = get_activity(user_id, activity_id)
    target_time = activity['amount'] * convert_unit_to_seconds(activity['unit'])

    running_activities[user_id].append(
        {**activity, 'started_at': datetime.utcnow(), 'target_time': target_time})


def stop_activity(user_id, activity_id):
    global running_activities

    if activity_id not in [x['id'] for x in get_running_activities(user_id)]:
        return

    running_activities[user_id] = [x for x in get_running_activities(user_id) if x['id'] != activity_id]


def get_activities(user_id):
    global temp_activities

    if not temp_activities.get(user_id):
        temp_activities[user_id] = []

    return temp_activities.get(user_id)


def add_activity(user_id, activity):
    global temp_activities

    temp_activities[user_id].append(activity)


def get_activity(user_id, activity_id):
    global temp_activities

    return [x for x in temp_activities[user_id] if x['id'] == activity_id][0]


def has_activity(user_id, activity_id):
    global temp_activities

    return len([x for x in temp_activities[user_id] if x['id'] == activity_id]) != 0


def delete_activity(user_id, activity_id):
    global temp_activities

    temp_activities[user_id] = [x for x in temp_activities[user_id] if x['id'] != activity_id]
