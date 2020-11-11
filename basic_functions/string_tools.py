# -*- coding: utf-8 -*-

import re


def split_camel_case(camel_case, sep=' ', to_list=False):
    # type: (str, str, bool) -> str or list
    """
    Split a camel-case string (likeThisOne) into its single components and use a specific separator

    :param camel_case: String to split
    :param sep: Separator for new string in case "to_list" == False
    :param to_list: Split string into a list of its single components
    :return: Either a new string with "sep" as the separator or a list of strings (in case "to_list" = True)
    """
    if to_list:
        return re.sub('([A-Z][a-z]+)', r'\1', re.sub('([A-Z]+)', r' \1'.format(sep=sep),
                                                     camel_case)).split()
    else:
        return re.sub('([A-Z][a-z]+)', r'\1', re.sub('([A-Z]+)', r'{sep}\1'.format(sep=sep),
                                                     camel_case)).lstrip(sep)


def replace_german_characters(text, encoding='utf8'):
    # type: (str, str) -> str
    """
    Replace special characters in string by their equivalent from the standard alphabet.
    Currently implemented are: \n
    ä, ö, ü, ß \n
    Adjust internal dictionary for further special characters.

    :param text:
    :param encoding:
    :return: String with replaced characters
    """
    replace_dict = {
        u'\xe4': 'ae',
        u'\xf6': 'oe',
        u'\xfc': 'ue',
        u'\xdf': 'ss'
    }
    try:
        text = text.decode(encoding)
    except UnicodeEncodeError:
        TypeError('Unable to decode text to {e}'.format(e=encoding))
    new_text = []
    if len(text) > 1:
        for l, literal in enumerate(text):
            if literal.lower() in replace_dict.keys():
                if literal != text[-1]:
                    if literal.isupper() and text[l+1].islower():
                        new_char = ''.join([replace_dict[literal.lower()][0].upper(),
                                            replace_dict[literal.lower()][1]])
                    elif literal.isupper() and text[l+1].isupper():
                        new_char = ''.join([replace_dict[literal.lower()][0].upper(),
                                            replace_dict[literal.lower()][1].upper()])
                    elif literal.islower() and text[l+1].islower():
                        new_char = ''.join([replace_dict[literal.lower()][0],
                                            replace_dict[literal.lower()][1]])
                    else:
                        if literal.lower() == u'\xdf':
                            if literal.islower() and text[l - 1].islower():
                                new_char = ''.join([replace_dict[literal.lower()][0],
                                                    replace_dict[literal.lower()][1]])
                            else:
                                new_char = ''.join([replace_dict[literal.lower()][0].upper(),
                                                    replace_dict[literal.lower()][1].upper()])
                        else:
                            new_char = ''
                            raise ValueError('Should not happen!')
                else:
                    if literal.lower() == u'\xdf':
                        if literal.islower() and text[l-1].islower():
                            new_char = ''.join([replace_dict[literal.lower()][0],
                                                replace_dict[literal.lower()][1]])
                        else:
                            new_char = ''.join([replace_dict[literal.lower()][0].upper(),
                                                replace_dict[literal.lower()][1].upper()])
                    else:
                        if literal.isupper():
                            new_char = ''.join([replace_dict[literal.lower()][0].upper(),
                                                replace_dict[literal.lower()][1].upper()])
                        else:
                            new_char = ''.join([replace_dict[literal.lower()][0],
                                                replace_dict[literal.lower()][1]])
                new_text.append(new_char)
            else:
                new_text.append(literal)
    else:
        if text.isupper():
            new_char = ''.join([replace_dict[text.lower()][0].upper(),
                                replace_dict[text.lower()][1].upper()])
        else:
            new_char = ''.join([replace_dict[text.lower()][0], replace_dict[text.lower()][1]])
        new_text.append(new_char)
    return ''.join(new_text)


if __name__ == '__main__':
    print(split_camel_case('TestCase', to_list=True))
