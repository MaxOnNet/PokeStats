"""accept-tos.py: Example script to accept in-game Terms of Service"""

from Interfaces.pgoapi import PGoApi
from Interfaces.pgoapi.utilities import f2i
from Interfaces.pgoapi import utilities as util
from Interfaces.pgoapi.exceptions import AuthException
import pprint
import time
import threading

def accept_tos(username, password):
	api = PGoApi()
	api.set_position(55.0467,73.3111,0.0)
	api.login('ptc', username, password)
	time.sleep(2)
	req = api.create_request()
	req.mark_tutorial_complete(tutorials_completed = 0, send_marketing_emails = False, send_push_notifications = False)
	response = req.call()
	print('Accepted Terms of Service for {}'.format(username))
	print('Response dictionary: \r\n{}'.format(pprint.PrettyPrinter(indent=4).pformat(response)))

for index in xrange(50):
    if index > 4:
        accept_tos("mapDefenderx{0}".format(index), "pwdxSf1{0}".format(index))
