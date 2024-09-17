#!/usr/bin/env sh

pip install coverage
coverage run manage.py test
coverage report -m --omit="manage.py,*/migrations/*,test_security_view.py,scheduled_call.py"
