temp_activities = {}


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
