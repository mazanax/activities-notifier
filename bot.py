import logging
import secrets

from telegram import ReplyKeyboardMarkup
from telegram.ext import Updater, ConversationHandler, CommandHandler, MessageHandler, Filters, RegexHandler

import db
from settings import API_TOKEN

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

logger = logging.getLogger(__name__)

buffer = {'create': {}, 'delete': {}}
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
 CONFIRM_DELETE_ACTIVITY) = range(7)


def start(_, update):
    global keyboards

    db.get_activities(update.message.from_user.id)  # TODO: delete when db will implemented

    update.message.reply_text(
        'Welcome! This is activity tracking bot\n\n' + HELP_STRING,
        reply_markup=ReplyKeyboardMarkup(keyboards['default'])
    )

    return MAIN_MENU


def cancel(_, update):
    global buffer

    buffer['create'].update({update.message.from_user.id: []})
    buffer['delete'].update({update.message.from_user.id: None})
    db.get_activities(update.message.from_user.id)

    update.message.reply_text(
        HELP_STRING,
        reply_markup=ReplyKeyboardMarkup(keyboards['default'])
    )

    return MAIN_MENU


def status(_, update):
    global keyboards

    running_activities = []

    update.message.reply_text(
        'No running activities found' if not running_activities else 'At this moment you have {0}{1}'.format(
            len(running_activities), 'activity' if len(running_activities) == 1 else 'activities'),
        reply_markup=ReplyKeyboardMarkup(keyboards['default'])
    )

    return MAIN_MENU


def show_activities_list(update):
    my_activities = db.get_activities(update.message.from_user.id)

    activities = [['START {id} ({title})'.format(**x)] for x in my_activities]
    activities.append(['CANCEL'])

    update.message.reply_html(
        'Here are your activities\n\n' + '\n'.join(
            ['• {id} <b>{title}</b> ({unit} {amount}) /del{id}'.format(**x) for x in my_activities]),
        reply_markup=ReplyKeyboardMarkup(activities)
    )


def activities_list(_, update):
    global keyboards

    my_activities = db.get_activities(update.message.from_user.id)

    if not my_activities:
        update.message.reply_text(
            'You haven\'t created any activity yet',
            reply_markup=ReplyKeyboardMarkup(keyboards['default'])
        )

        return MAIN_MENU
    else:
        show_activities_list(update)

        return START_ACTIVITY


def delete_activity(_, update):
    global keyboards

    user_id = update.message.from_user.id
    activity_id = update.message.text[4:]

    if db.has_activity(user_id, activity_id):
        update.message.reply_text(
            'Are you sure that you wanna delete activity {}?'.format(
                db.get_activity(user_id, activity_id).get('title')),
            reply_markup=ReplyKeyboardMarkup(keyboards['confirm'])
        )

        buffer['delete'][update.message.from_user.id] = activity_id

        return CONFIRM_DELETE_ACTIVITY
    else:
        update.message.reply_text(
            'Activity {} has been deleted'.format(activity_id),
            reply_markup=ReplyKeyboardMarkup(keyboards['default'])
        )

        activities_list(_, update)

        return START_ACTIVITY


def confirm_delete_activity(_, update):
    global keyboards

    db.delete_activity(update.message.from_user.id, buffer['delete'][update.message.from_user.id])

    update.message.reply_text(
        'Activity {} has been deleted'.format(buffer['delete'][update.message.from_user.id]),
        reply_markup=ReplyKeyboardMarkup(keyboards['default'])
    )

    del buffer['delete'][update.message.from_user.id]

    return activities_list(_, update)


def activities_add(_, update):
    global keyboards

    update.message.reply_text(
        'Send activity title',
        reply_markup=ReplyKeyboardMarkup(keyboards['cancel'])
    )

    return ADD_ACTIVITY_TIME_UNIT


def activities_add_set_time_unit(_, update):
    global keyboards

    buffer['create'][update.message.from_user.id] = {'id': secrets.token_hex(3), 'title': update.message.text}

    update.message.reply_text(
        'How long does this activity last?',
        reply_markup=ReplyKeyboardMarkup(keyboards['time_units'])
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
            reply_markup=ReplyKeyboardMarkup(keyboards['time_units'])
        )

        return ADD_ACTIVITY_TIME

    update.message.reply_text(
        'Please specify how much {} (min: {}, max: {}) activity will last'.format(unit, *interval),
        reply_markup=ReplyKeyboardMarkup(keyboards['cancel'])
    )

    return ADD_ACTIVITY_TIME_DONE


def activities_add_done(_, update):
    global keyboards

    unit = buffer['create'][update.message.from_user.id].get('unit')
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
            reply_markup=ReplyKeyboardMarkup(keyboards['time_units'])
        )

        return ADD_ACTIVITY_TIME

    if amount < interval[0] or amount > interval[1]:
        update.message.reply_text(
            'Amount should be greater or equal than {} and less or equal than {}'.format(*interval),
            reply_markup=ReplyKeyboardMarkup(keyboards['cancel'])
        )

        return ADD_ACTIVITY_TIME_DONE

    buffer['create'][update.message.from_user.id].update({'amount': amount})
    db.add_activity(update.message.from_user.id, buffer['create'][update.message.from_user.id])

    update.message.reply_text(
        'Activity successfully added',
        reply_markup=ReplyKeyboardMarkup(keyboards['default'])
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
            RegexHandler('^CANCEL$', cancel)
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
                # RegexHandler('^START ', start_activity)
            ],
            CONFIRM_DELETE_ACTIVITY: [
                RegexHandler('^CANCEL$', activities_list),
                RegexHandler('^CONFIRM$', confirm_delete_activity),
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
    main()
