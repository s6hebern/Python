import sys


def ask_user(question, default='yes'):
    # type: (str, str) -> bool
    """Ask a yes/no question via raw_input() and return the answer.

    Example:\n
    answer = query_yes_no('Are you sure?') \n
    if answer is True:
        print 'I agree!'
    else:
        print 'User abort!'

    :param question: a string that is presented to the user.
    :param default: the presumed answer if the user just hits <Enter>.
        It must be "yes" (the default), "no" or None (meaning
        an answer is required from the user).
    :return: True for "yes", False for "no".
    """
    valid = {'yes': True, 'y': True, 'ye': True,
             'no': False, 'n': False}
    if default is None:
        prompt = ' [y/n] '
    elif default.lower() == 'yes':
        prompt = ' [Y/n] '
    elif default.lower() == 'no':
        prompt = ' [y/N] '
    else:
        raise ValueError('invalid default answer: "{d}"'.format(d=default))
    while True:
        sys.stdout.write(question + prompt)
        choice = raw_input().lower()
        if default is not None and choice == '':
            return valid[default.lower()]
        elif choice in valid:
            return valid[choice]
        else:
            sys.stdout.write("Please respond with 'yes' or 'no' "
                             "(or 'y' or 'n').\n")
