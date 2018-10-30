from os import getenv

from dotenv import load_dotenv

load_dotenv()

API_TOKEN = getenv('API_TOKEN')

DB_USER = getenv('POSTGRES_USER')
DB_PASS = getenv('POSTGRES_PASSWORD')
DB_NAME = getenv('POSTGRES_DB')
DB_HOST = getenv('POSTGRES_HOST')
DB_PORT = getenv('POSTGRES_PORT')
