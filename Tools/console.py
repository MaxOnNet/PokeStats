import argparse
import sys

from Tools.accountcreator import *
from Tools.ptcexceptions import *


for index in xrange(2):
    try:
        print (index)
        # Create the random account
        account_info = create_account(
            "mapDefender-x{0}".format(index), "pwd-x-{0}".format(index), "mapDefender-{0}@tatarnikov.org".format(index)
        )


        print """INSERT INTO `db_pokestats`.`scanner_account` (`username`, `password`, `service`, `is_enable`, `is_active`) VALUES ('{0}', '{1}', 'ptc', '1', '0');""".format(account_info[USERNAME], account_info[PASSWORD])
    # Handle account creation failure exceptions
    except PTCInvalidPasswordException as err:
        print('Invalid password: {}'.format(err))
    except (PTCInvalidEmailException, PTCInvalidNameException) as err:
        print('Failed to create account! {}'.format(err))
    except PTCException as err:
        print('Failed to create account! General error:  {}'.format(err))
