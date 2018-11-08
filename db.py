from datetime import datetime

from models import User, Activity, RunningActivity


def find_user_or_create(from_user):
    user = User.select().where(User.telegram_id == from_user.id)

    if not user.exists():
        user = User.create(telegram_id=from_user.id, username=from_user.username)
    else:
        user = user.get()

    return user


def get_running_activities(from_user):
    running_activities = RunningActivity.select().join(User).where(User.telegram_id == from_user.id,
                                                                   RunningActivity.notified_at.is_null(),
                                                                   RunningActivity.started_at < datetime.now())

    return [] if not running_activities.exists() else list(running_activities)


def get_all_running_activities():
    running_activities = RunningActivity.select().where(RunningActivity.notified_at.is_null())

    return [] if not running_activities.exists() else list(running_activities)


def get_running_activity(from_user, activity_id):
    return RunningActivity.select().join(User).where(User.telegram_id == from_user.id,
                                                     RunningActivity.notified_at.is_null(),
                                                     RunningActivity.activity_id == activity_id).get()


def has_running_activity(from_user, activity_id):
    return RunningActivity.select().join(User).where(User.telegram_id == from_user.id,
                                                     RunningActivity.notified_at.is_null(),
                                                     RunningActivity.activity_id == activity_id).exists()


def start_activity(from_user, activity_id):
    def convert_unit_to_seconds(unit):
        if unit == 'MINUTES':
            return 60
        elif unit == 'HOURS':
            return 3600
        elif unit == 'DAYS':
            return 86400
        else:
            raise RuntimeError('Unknown unit {}'.format(unit))

    if has_running_activity(from_user, activity_id):
        return

    activity = get_activity(from_user, activity_id)
    total_time = activity.amount * convert_unit_to_seconds(activity.unit)

    RunningActivity.create(activity_id=activity_id, title=activity.title, unit=activity.unit, amount=activity.amount,
                           user=activity.user, started_at=datetime.utcnow(), total_time=total_time)


def stop_activity(from_user, activity_id):
    if not has_running_activity(from_user, activity_id):
        return

    get_running_activity(from_user, activity_id).delete_instance()


def get_activities(from_user):
    activities = Activity.select().join(User).where(User.telegram_id == from_user.id)

    return activities.dicts()


def add_activity(from_user, activity):
    Activity.create(user=find_user_or_create(from_user), **activity)


def get_activity(from_user, activity_id):
    activity = Activity.select().join(User).where(User.telegram_id == from_user.id, Activity.activity_id == activity_id)

    if not activity.exists():
        return None

    return activity.get()


def has_activity(from_user, activity_id):
    return get_activity(from_user, activity_id) is not None


def delete_activity(from_user, activity_id):
    activity = get_activity(from_user, activity_id)

    activity.delete_instance()
