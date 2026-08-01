# KAIRYX Bot

## Railway deploy

1. Push this repository to GitHub.
2. Create a new Railway project and connect the repository.
3. Set these environment variables:
   - BOT_TOKEN
   - DATABASE_URL (or POSTGRES_* variables)
   - REDIS_URL (recommended) or REDIS_HOST / REDIS_PORT
   - ADMIN_IDS
4. Railway will start the bot using the Procfile.
