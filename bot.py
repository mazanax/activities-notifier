import logging
import secrets

from playhouse.shortcuts import model_to_dict
from telegram import ReplyKeyboardMarkup
from telegram.ext import Updater, ConversationHandler, CommandHandler, MessageHandler, Filters, RegexHandler

import db
from settings import API_TOKEN
from models import db as postgres, User, Activity, RunningActivity

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

logger = logging.getLogger(__name__)

buffer = {'create': {}, 'delete': {}, 'stop': {}}
keyboards = {
    'default': [['STATUS'], ['LIST', 'ADD NEW']],
    'time_units': [['MINUTES', 'HOURS', 'DAYS'], ['CANCEL']],
    'confirm': [['CONFIRM'], ['CANCEL']],
    'cancel': [['CANCEL']],
}
HELP_STRING = '''Press STATUS to get list of running activities\n
Press LIST to get list of all available activities\n
Press ADD NEW to create new activity\n\n
You will get notifications when activity expires'''

(MAIN_MENU, STATUS, ADD_ACTIVITY_TIME, ADD_ACTIVITY_TIME_UNIT, ADD_ACTIVITY_TIME_DONE, START_ACTIVITY,
 CONFIRM_DELETE_ACTIVITY, STOP_ACTIVITY, CONFIRM_STOP_ACTIVITY) = range(9)


def start(_, update):
    global keyboards

    db.find_user_or_create(update.message.from_user)

    update.message.reply_text(
        'Welcome! This is activity tracking bot\n\n' + HELP_STRING,
        reply_markup=ReplyKeyboardMarkup(keyboards['default'], one_time_keyboard=True, resize_keyboard=True)
    )

    return MAIN_MENU


def cancel(_, update):
    global buffer

    user_id = update.message.from_user.id

    buffer['create'].update({user_id: []})
    buffer['delete'].update({user_id: None})
    buffer['stop'].update({user_id: None})

    update.message.reply_text(
        HELP_STRING,
        reply_markup=ReplyKeyboardMarkup(keyboards['default'], one_time_keyboard=True, resize_keyboard=True)
    )

    return MAIN_MENU


def status(_, update):
    global keyboards

    running_activities = db.get_running_activities(update.message.from_user)

    if not running_activities:
        update.message.reply_text(
            'No running activities found',
            reply_markup=ReplyKeyboardMarkup(keyboards['default'], one_time_keyboard=True, resize_keyboard=True)
        )

        return MAIN_MENU
    else:
        update.message.reply_html(
            'At this moment you have {0}{1}\n\n'.format(
                len(running_activities), 'activity' if len(running_activities) == 1 else 'activities') + '\n'.join(
                ['• {activity_id} <b>{title}</b> ({unit} {amount}): {progress}% /stop{activity_id}'.format(
                    progress=x.progress, **model_to_dict(x))
                 for x in running_activities]),
            reply_markup=ReplyKeyboardMarkup(keyboards['default'], one_time_keyboard=True, resize_keyboard=True)
        )

        return STOP_ACTIVITY


def stop_activity(_, update):
    global keyboards

    from_user = update.message.from_user
    activity_id = update.message.text[5:]

    if db.has_activity(from_user, activity_id):
        update.message.reply_html(
            'Are you sure that you wanna stop activity <b>{}</b>?'.format(
                db.get_activity(from_user, activity_id).title),
            reply_markup=ReplyKeyboardMarkup(keyboards['confirm'], one_time_keyboard=True, resize_keyboard=True)
        )

        buffer['stop'][from_user.id] = activity_id

        return CONFIRM_STOP_ACTIVITY
    else:
        update.message.reply_text(
            'Activity {} has been stopped'.format(activity_id),
            reply_markup=ReplyKeyboardMarkup(keyboards['default'], one_time_keyboard=True, resize_keyboard=True)
        )

        status(_, update)

        return STOP_ACTIVITY


def confirm_stop_activity(_, update):
    global keyboards

    from_user = update.message.from_user

    db.stop_activity(from_user, buffer['stop'][from_user.id])

    update.message.reply_text(
        'Activity {} has been stopped'.format(buffer['stop'][from_user.id]),
        reply_markup=ReplyKeyboardMarkup(keyboards['default'], one_time_keyboard=True, resize_keyboard=True)
    )

    del buffer['stop'][from_user.id]

    return status(_, update)


def show_activities_list(update):
    from_user = update.message.from_user

    my_activities = db.get_activities(from_user)

    activities = [['START {activity_id} ({title})'.format(**x)] for x in my_activities if
                  not db.has_running_activity(from_user, x['activity_id'])]
    activities.append(['CANCEL'])

    update.message.reply_html(
        'Here are your activities\n\n' + '\n'.join(
            ['• {activity_id} <b>{title}</b> ({unit} {amount}) /del{activity_id}'.format(**x) for x in my_activities]),
        reply_markup=ReplyKeyboardMarkup(activities, one_time_keyboard=True, resize_keyboard=True)
    )


def activities_list(_, update):
    global keyboards

    my_activities = db.get_activities(update.message.from_user)

    if not my_activities:
        update.message.reply_text(
            'You haven\'t created any activity yet',
            reply_markup=ReplyKeyboardMarkup(keyboards['default'], one_time_keyboard=True, resize_keyboard=True)
        )

        return MAIN_MENU
    else:
        show_activities_list(update)

        return START_ACTIVITY


def delete_activity(_, update):
    global keyboards

    from_user = update.message.from_user
    activity_id = update.message.text[4:]

    if db.has_activity(from_user, activity_id):
        update.message.reply_html(
            'Are you sure that you wanna delete activity <b>{}</b>?'.format(
                db.get_activity(from_user, activity_id).title),
            reply_markup=ReplyKeyboardMarkup(keyboards['confirm'])
        )

        buffer['delete'][from_user.id] = activity_id

        return CONFIRM_DELETE_ACTIVITY
    else:
        update.message.reply_text(
            'Activity {} has been deleted'.format(activity_id),
            reply_markup=ReplyKeyboardMarkup(keyboards['default'], one_time_keyboard=True, resize_keyboard=True)
        )

        activities_list(_, update)

        return START_ACTIVITY


def confirm_delete_activity(_, update):
    global keyboards

    from_user = update.message.from_user

    db.delete_activity(from_user, buffer['delete'][from_user.id])

    update.message.reply_text(
        'Activity {} has been deleted'.format(buffer['delete'][from_user.id]),
        reply_markup=ReplyKeyboardMarkup(keyboards['default'], one_time_keyboard=True, resize_keyboard=True)
    )

    del buffer['delete'][from_user.id]

    return activities_list(_, update)


def start_activity(_, update):
    global keyboards

    activity_id = update.message.text.split(' ')[1]

    db.start_activity(update.message.from_user, activity_id)

    update.message.reply_text(
        'Activity {} has been started'.format(activity_id)
    )

    return status(_, update)


def activities_add(_, update):
    global keyboards

    update.message.reply_text(
        'Send activity title',
        reply_markup=ReplyKeyboardMarkup(keyboards['cancel'], one_time_keyboard=True, resize_keyboard=True)
    )

    return ADD_ACTIVITY_TIME_UNIT


def activities_add_set_time_unit(_, update):
    global keyboards

    buffer['create'][update.message.from_user.id] = {'activity_id': secrets.token_hex(3), 'title': update.message.text}

    update.message.reply_text(
        'How long does this activity last?',
        reply_markup=ReplyKeyboardMarkup(keyboards['time_units'], one_time_keyboard=True, resize_keyboard=True)
    )

    return ADD_ACTIVITY_TIME


def activities_add_set_time(_, update):
    global keyboards

    unit = update.message.text
    buffer['create'][update.message.from_user.id].update({'unit': unit})

    if unit == 'MINUTES':
        interval = [1, 59]
    elif unit == 'HOURS':
        interval = [1, 23]
    elif unit == 'DAYS':
        interval = [1, 6]
    else:
        update.message.reply_text(
            'Unknown time unit\n\nHow long does this activity last?',
            reply_markup=ReplyKeyboardMarkup(keyboards['time_units'], one_time_keyboard=True, resize_keyboard=True)
        )

        return ADD_ACTIVITY_TIME

    update.message.reply_text(
        'Please specify how much {} (min: {}, max: {}) activity will last'.format(unit, *interval),
        reply_markup=ReplyKeyboardMarkup(keyboards['cancel'], one_time_keyboard=True, resize_keyboard=True)
    )

    return ADD_ACTIVITY_TIME_DONE


def activities_add_done(_, update):
    global keyboards

    from_user = update.message.from_user
    unit = buffer['create'][from_user.id].get('unit')
    amount = int(update.message.text)

    if unit == 'MINUTES':
        interval = [1, 59]
    elif unit == 'HOURS':
        interval = [1, 23]
    elif unit == 'DAYS':
        interval = [1, 6]
    else:
        update.message.reply_text(
            'Unknown time unit\n\n'
            'How long does this activity last?',
            reply_markup=ReplyKeyboardMarkup(keyboards['time_units'], one_time_keyboard=True, resize_keyboard=True)
        )

        return ADD_ACTIVITY_TIME

    if amount < interval[0] or amount > interval[1]:
        update.message.reply_text(
            'Amount should be greater or equal than {} and less or equal than {}'.format(*interval),
            reply_markup=ReplyKeyboardMarkup(keyboards['cancel'], one_time_keyboard=True, resize_keyboard=True)
        )

        return ADD_ACTIVITY_TIME_DONE

    buffer['create'][from_user.id].update({'amount': amount})
    db.add_activity(from_user, buffer['create'][from_user.id])

    update.message.reply_text(
        'Activity successfully added',
        reply_markup=ReplyKeyboardMarkup(keyboards['default'], one_time_keyboard=True, resize_keyboard=True)
    )

    return MAIN_MENU


def error(_, update, error_):
    """Log Errors caused by Updates."""
    logger.warning('Update "%s" caused error "%s"', update, error_)


def main():
    if not API_TOKEN:
        print('You should specify telegram api token in .env file')
        exit(1)

    updater = Updater(API_TOKEN)
    dp = updater.dispatcher

    conversation_handler = ConversationHandler(
        entry_points=[
            CommandHandler('start', start),
            CommandHandler('cancel', cancel),
            MessageHandler(Filters.text, cancel)
        ],

        states={
            MAIN_MENU: [
                RegexHandler('^STATUS$', status),
                RegexHandler('^LIST$', activities_list),
                RegexHandler('^ADD NEW$', activities_add),
                RegexHandler('^CANCEL$', cancel)
            ],
            START_ACTIVITY: [
                RegexHandler('^CANCEL$', cancel),
                RegexHandler('^/del', delete_activity),
                RegexHandler('^START ', start_activity)
            ],
            CONFIRM_DELETE_ACTIVITY: [
                RegexHandler('^CANCEL$', activities_list),
                RegexHandler('^CONFIRM$', confirm_delete_activity),
            ],
            STOP_ACTIVITY: [
                RegexHandler('^STATUS$', status),
                RegexHandler('^LIST$', activities_list),
                RegexHandler('^ADD NEW$', activities_add),
                RegexHandler('^/stop', stop_activity)
            ],
            CONFIRM_STOP_ACTIVITY: [
                RegexHandler('^CANCEL$', status),
                RegexHandler('^CONFIRM$', confirm_stop_activity),
            ],
            ADD_ACTIVITY_TIME_UNIT: [
                RegexHandler('^CANCEL$', cancel),
                MessageHandler(Filters.text, activities_add_set_time_unit)
            ],
            ADD_ACTIVITY_TIME: [
                RegexHandler('^MINUTES$', activities_add_set_time),
                RegexHandler('^HOURS$', activities_add_set_time),
                RegexHandler('^DAYS$', activities_add_set_time),
                RegexHandler('^CANCEL$', cancel)
            ],
            ADD_ACTIVITY_TIME_DONE: [
                RegexHandler('^CANCEL$', cancel),
                MessageHandler(Filters.text, activities_add_done)
            ]
        },

        fallbacks=[
            CommandHandler('cancel', cancel),
            RegexHandler('^CANCEL$', cancel)
        ]
    )

    dp.add_handler(conversation_handler)
    dp.add_error_handler(error)

    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    with postgres:
        postgres.create_tables([User, Activity, RunningActivity], safe=True)

    main()
