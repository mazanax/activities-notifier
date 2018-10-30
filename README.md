# Activities Notifier

It's a telegram bot that allows you to create list of repeating activities with duration. For example you wanna be notified when your lunch ends.

## Installation

1. You need to get BOT TOKEN from `BotFather` (https://t.me/BotFather)
2. Copy `.env.dist` to `.env`
3. Specify credentials of your database at `.env`. For example:
```
POSTGRES_USER=postgres
POSTGRES_PASSWORD=123456
POSTGRES_DB=db
POSTGRES_HOST=127.0.0.1
POSTGRES_PORT=5432
```
4. Paste BOT TOKEN as a value of `API_TOKEN` variable. For example:
```
API_TOKEN=1488:U3VwZXItUHVwZXItU2VjcmV0LVRva2VuLU9mLVlvdXItQm90
```
5. Run `bot.py`
6. Run `worker.py` (not implemented yet)
7. Go to your bot and type `/start`

## Scheme of telegram bot

![Scheme of bot](../assets/scheme.png?raw=true)
