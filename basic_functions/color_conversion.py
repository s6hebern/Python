import colorsys
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors


def show_colorbar(colors, labels=None, width=10, height=5, side_ratio=10):
    # type: (tuple, tuple, int, int, int) -> None
    """
    Plot a colorbar of given colors and their labels

    :param colors: Tuple of RGB tuples
    :param labels: Tuple of color names
    :param width: Width of colorbar in inches
    :param height: Height of colorbar in inches
    :param side_ratio: Ratio of width to height
    :return: --
    """
    if not side_ratio:
        side_ratio = float(width) / float(height)
    sections = len(colors)
    # normalize greyvalues
    norm = plt.Normalize(0, 256)
    # map greyvalues to respective color
    scaled_colors = []
    for rgb in colors:
        scaled_colors.append(tuple([float(c) / 255. for c in rgb]))
    mappings = list(zip(map(norm, [i for i in np.linspace(0, 256, sections)]), scaled_colors))
    if sections < 2:
        mappings.append((1., mappings[0][1]))
    colorbar = mcolors.LinearSegmentedColormap.from_list('', mappings)
    x_vals = np.arange(0, 256, 256. / sections)
    a = np.asarray((([int(i) for i in x_vals],) * int(side_ratio)))
    # create plot
    plt.figure(figsize=(width, height))
    img = plt.imshow(a, interpolation='nearest')
    img.set_cmap(colorbar)
    axes = plt.gca()
    x_axis = axes.get_xaxis()
    y_axis = axes.get_yaxis()
    if labels:
        x_axis.set_visible(True)
        axes.set_xticklabels(labels)
    else:
        x_axis.set_visible(False)
    y_axis.set_visible(False)
    plt.tight_layout()
    plt.show()
    return


def hex_to_rgb(hex_code):
    # type: (str) -> (int, int, int)
    """
    Convert HEX to RGB color codes

    Example: hex_to_rgb('#FFFFFF') --> (255, 255, 255)

    :param str hex_code: Color as hex-code including hash sign (e.g. '#FFFFFF')
    :return: Tuple of integers for RGB
    """
    # Pass 16 to the integer function for change of base
    rgb_list = [int(hex_code[i:i + 2], 16) for i in range(1, 6, 2)]
    return tuple(rgb_list)


def rgb_to_hex(rgb, to_upper=True, hash=True):
    # type: (tuple, bool, bool) -> str
    """
    Convert RGB to HEX color codes

    :param rgb: HEX color code, e.g. '#FFFFFF'
    :param to_upper: Make HEX color code uppercase
    :param hash: Include hash sign in HEX color code
    :return: HEX color code
    """
    hexa = '#%02x%02x%02x' % rgb if hash else '%02x%02x%02x' % rgb
    if to_upper is True:
        hexa = hexa.upper()
    print('RGB: {rgb} \t HEX: {hexa}'.format(rgb=rgb, hexa=hexa))
    return hexa


def hex_to_hsv(hex_color):
    # type: (str) -> (int, int, int)
    """
    Convert HEX to HSV color codes

    :param hex_color: HEX color code, e.g. '#FFFFFF'
    :return: HSV color code
    """
    hex_color = hex_color.lstrip('#')  # in case you have Web color specs
    r, g, b = (int(hex_color[i:i + 2], 16) / 255.0 for i in xrange(0, 5, 2))
    hsv = colorsys.rgb_to_hsv(r, g, b)
    return hsv


def hsv_to_rgb(hsv):
    # type: (tuple) -> (int, int, int)
    """
    Convert HSV to RGB color codes

    :param hsv: Tuple of HSV color codes
    :return: Tuple of RGB color codes
    """
    h, s, v = hsv
    rgb = colorsys.hsv_to_rgb(h, s, v)
    rgb = tuple([int(255 * i) for i in rgb])
    return rgb


def linear_color_gradient(start_hex, end_hex, n):
    # type: (str, str, int) -> list
    """
    Returns a gradient list of (n) colors between two hex colors. start_hex and end_hex should be
    the full six-digit color string, including the hash sign ('#FFFFFF').

    :param str start_hex: First color as hex-code including hash sign (e.g. '#FFFFFF')
    :param str end_hex: Last color as hex-code including hash sign (e.g. '#FFFFFF')
    :param int n: Number of colors (at least 2, which would only be start_hex and end_hex as RGB
            values)
    :return: List of RGB colors (as tuple of integers)
    """
    if n < 2:
        raise ValueError('Parameter "n" has to be at least 2!')
    start_rgb = hex_to_rgb(start_hex)
    end_rgb = hex_to_rgb(end_hex)
    print('First color: \n\t HEA: {hexcol} \t RGB: {rgbcol}'.format(hexcol=start_hex,
                                                                    rgbcol=start_rgb))
    print('Last color: \n\t HEX: {hexcol} \t RGB: {rgbcol}'.format(hexcol=end_hex, rgbcol=end_rgb))
    # Initialize a list of the output colors with the starting color
    rgb_list = [start_rgb]
    # Calcuate a color at each evenly spaced value of c from 1 to n
    for c in range(1, n):
        # Interpolate RGB values for each color at the current value of c
        rgb = [int(start_rgb[i] + (float(c) / (n - 1)) * (end_rgb[i] - start_rgb[i])) for i in range(3)]
        rgb = tuple(rgb)
        # Add it to our list of output colors
        rgb_list.append(rgb)
    return rgb_list


if __name__ == '__main__':
    start = '#F2F2F2'.upper()
    end = '#4B4B4D'.upper()
    rgb = linear_color_gradient(start, end, n=5)
    print rgb_to_hex(rgb[1]).upper()
    print rgb_to_hex(rgb[2]).upper()
    print rgb_to_hex(rgb[3]).upper()
    print rgb_to_hex((40, 40, 42))
