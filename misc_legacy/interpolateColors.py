def hex2RGB(hex_code):
    """
    Convert hex-color to RGB

    :param str hex_code: Color as hex-code including hash sign (e.g. '#FFFFFF')
    :return: Tuple of integers for RGB
    :rtype: tuple
    :example: hex2RGB('#FFFFFF') --> [255,255,255]
    """

    # Pass 16 to the integer function for change of base
    rgb_list = [int(hex_code[i:i + 2], 16) for i in range(1, 6, 2)]
    return tuple(rgb_list)


def linearColorGradient(start_hex, end_hex, n):
    """
    Returns a gradient list of (n) colors between two hex colors. start_hex and end_hex should be the full six-digit
    color string, including the hash sign ('#FFFFFF').

    :param str start_hex: First color as hex-code including hash sign (e.g. '#FFFFFF')
    :param str end_hex: Last color as hex-code including hash sign (e.g. '#FFFFFF')
    :param int n: Number of colors (at least 2, which would only be start_hex and end_hex as RGB values)
    :return: List of RGB colors (as tuple of integers)
    :rtype: list
    """

    if n < 2:
        raise ValueError('Parameter "n" has to be at least 2!')
    s = hex2RGB(start_hex)
    f = hex2RGB(end_hex)
    print 'First color: \n\t HEX: {hexcol} \t RGB: {rgbcol}'.format(hexcol=start_hex, rgbcol=s)
    print 'Last color: \n\t HEX: {hexcol} \t RGB: {rgbcol}'.format(hexcol=end_hex, rgbcol=f)
    # Initialize a list of the output colors with the starting color
    RGB_list = [s]
    # Calcuate a color at each evenly spaced value of t from 1 to n
    for t in range(1, n):
        # Interpolate RGB vector for color at the current value of t
        curr_vector = tuple([int(s[j] + (float(t) / (n - 1)) * (f[j] - s[j])) for j in range(3)])
        # Add it to our list of output colors
        RGB_list.append(curr_vector)
    return RGB_list


if __name__ == '__main__':
    start = '#7d7d7d'.upper()
    end = '#be8c14'.upper()
    print linearColorGradient(start, end, n=5)
