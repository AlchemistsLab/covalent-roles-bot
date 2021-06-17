# Covalent Discord Roles Bot

A bot that can assign roles based on Covalent website data


## Installation
1. [Install Docker](https://docs.docker.com/engine/install/ubuntu/)
2. Copy and update settings in `.env.example`
3. Execute `docker-compose up -d`
4. Install requirements from `requirements.txt` for `>= Python 3.6`
5. Copy and update settings in `config.example.py`
6. Init database tables via `aerich upgrade`
7. We will need to create account and get `Bearer token` and save it to `config.py`
8. Start bot via `python bot.py` or [via supervisord](http://supervisord.org/) or [systemd](https://es.wikipedia.org/wiki/Systemd)
9. Add a bot to the server with administrator permissions


## First run
- to prevent spamming existing users about their promotion during the first run set `DO_SEND_NOTIFICATIONS` to `False`, give it a couple of minutes to create necessary rows in the database and then restart the bot with `DO_SEND_NOTIFICATIONS` set to `True`


## How it works
- bot watches Covalent website for CQT points
- when a user reaches the threshold it will be promoted to the Apprentice/Valiant/Master role
- the bot will also send a notification to the channel to greet the user
