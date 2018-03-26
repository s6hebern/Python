import sys

def askUser(question, default="yes"):
    """Ask a yes/no question via raw_input() and return the answer.

    :param string question: a string that is presented to the user.
    :param string default: the presumed answer if the user just hits <Enter>.
        It must be "yes" (the default), "no" or None (meaning
        an answer is required from the user).

    :return: True for "yes", False for "no".
    :rtype: bool

    Example:\n
    answer = askUser('Are you sure?') \n
    if answer is True:
        print 'I agree!'
    else:
        print 'User abort!'
    """
    valid = {"yes": True, "y": True, "ye": True,
             "no": False, "n": False}
    if default is None:
        prompt = " [y/n] "
    elif default == "yes":
        prompt = " [Y/n] "
    elif default == "no":
        prompt = " [y/N] "
    else:
        raise ValueError("invalid default answer: '%s'" % default)

    while True:
        sys.stdout.write(question + prompt)
        choice = raw_input().lower()
        if default is not None and choice == '':
            return valid[default]
        elif choice in valid:
            return valid[choice]
        else:
            sys.stdout.write("Please respond with 'yes' or 'no' "
                             "(or 'y' or 'n').\n")

# print askUser('Do you really want to proceed?', None)
