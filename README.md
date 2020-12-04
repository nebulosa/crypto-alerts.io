About
-----

Get notified when a coin goes above or below a price target, [crypto-alerts.io](https://crypto-alerts.io/).

Supported Exchanges
-------------------

- [Binance](https://binance.com)
- [Bitso](https://bitso.com)

Usage
-----

    #config
    $ echo 'APP_DOMAIN=crypto-alerts.io'         >  .env
    $ echo 'APP_ADMIN=admin@crypto-alerts.io'   >>  .env
    $ echo 'APP_TITLE=Crypt Alerts'             >>  .env

    $ echo 'APP_FROM=no-reply@crypto-alerts.io' >>  .env

    $ echo 'APP_MAX_ALERTS_PER_MONTH=100'       >>  .env
    $ echo 'APP_MAX_EMAIL_NOTIFICATIONS_PER_MONTH=1000' >> .env
    $ echo 'APP_MAX_ALERTS_SPAM_STRIKES=3'      >>  .env

    $ echo 'SMTP_SERVER=smtp.crypto-alerts.io'  >>  .env
    $ echo 'SMTP_PORT=25'                       >>  .env
    $ echo 'SMTP_USERNAME=no-reply@crypto-alerts.io' >>  .env
    $ echo 'SMTP_PASSWORD=passwd'               >>  .env
    $ echo 'SMTP_USE_TLS=yes'                   >>  .env

    $ echo 'RECAPTCHA_PUBLIC_KEY=key'       >> .env
    $ echo 'RECAPTCHA_PRIVATE_KEY=key'      >> .env

    #app's development
    $ ./setup.sh [docker-compose-file]

Access http://localhost:5000

    #provision's development (ansible recipes: docker/docker-compose/multisite setup)
    $ vagrant up
    $ ANSIBLE_ARGS="--tags upload" vagrant provision #fast-forward (only update app's code)

Access http://dev.crypto-alerts.io

    #production, requires an Ubuntu >= 18.04 LTS box with root ssh credential access
    $ vim provision/ansible/inventories/prod/hosts
    $ ./deploy.sh prod

    #production fast-forward (only updates app's code)
    $ ./deploy-fast-forward.sh prod

Access http://crypto-alerts.io or the configured production domain

Dependencies
------------

- [docker](https://www.docker.com/)
- [docker-compose](https://docs.docker.com/compose/)

If you're interested in modifying the provision/ansible recipes you'll also need:

- [vagrant](https://www.vagrantup.com/)
- [ansible](https://www.ansible.com/)
