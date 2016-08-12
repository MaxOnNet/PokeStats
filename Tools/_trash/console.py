from Tools.ptcexceptions import *

from Tools._trash.accountcreator import *


# 	clubmap9   v

# account_info = create_account(
#            "clubmap{0}".format(index), "pwdxSf1{0}".format(index), "v{0}@tatarnikov.org".format(index)
#        )
for index in xrange(300):
    if index < 200:
        pass
    else:
        status = 0
        while status == 0:
            try:

                account_info = create_account(
                    "mapDefenderx{0}".format(index), "pwdxSf1{0}".format(index), "mapDefender-{0}@tatarnikov.org".format(index)
                )

                print """INSERT INTO `db_pokestats`.`scanner_account` (`username`, `password`, `service`, `is_enable`, `is_active`) VALUES ('{0}', '{1}', 'ptc', '1', '0');""".format("mapDefenderx{0}".format(index), "pwdxSf1{0}".format(index))
                status = 1
            # Handle account creation failure exceptions
            except PTCInvalidPasswordException as err:
                print('Invalid password: {}'.format(err))
            except (PTCInvalidEmailException, PTCInvalidNameException) as err:
                print('Failed to create account! {}'.format(err))
                status = 1
            except PTCException as err:
                print('Failed to create account! General error:  {}'.format(err))
# 51
