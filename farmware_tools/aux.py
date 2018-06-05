#!/usr/bin/env python

'''Farmware Tools: Auxiliary Utilities.'''

from __future__ import print_function

class Color(object):
    """Color codes for colorizing terminal output."""

    def __init__(self):
        self.green = self.get_color_code('green')
        self.red = self.get_color_code('red')
        self.yellow = self.get_color_code('yellow')
        self.magenta = self.get_color_code('magenta')
        self.cyan = self.get_color_code('cyan')
        self.blue = self.get_color_code('blue')
        self.bold = self.get_color_code('bold')
        self.reset = self.get_color_code('reset')

    color_number = {
        'green': 32,
        'red': 31,
        'yellow': 33,
        'magenta': 35,
        'cyan': 36,
        'blue': 34,
        'reset': 0,
        'bold': 1,
        }

    def get_color_code(self, string):
        """Get a color code to use in a string.

        Args:
            string (str): Color name (key of color_number).
        """
        return '\033[{}m'.format(self.color_number[string])

    def colorize_celery_script(self, kind, args, body=None):
        """Color terminal printing of Celery Script.

        Args:
            kind (str): Celery Script kind.
            args (dict): Celery Script args.
            body (list, optional): Celery Script body. Defaults to None.
        """
        colorized_kind = "'kind': '{magenta}{kind}{reset}'".format(
            magenta=self.magenta, kind=kind, reset=self.reset)
        colorized_args = ", 'args': {cyan}{args}{reset}".format(
            cyan=self.cyan, args=args, reset=self.reset)
        colorized_body = ", 'body': {blue}{body}{reset}".format(
            blue=self.blue, body=body, reset=self.reset)
        to_print = "{{{kind}{args}{body}}}".format(
            kind=colorized_kind,
            args=colorized_args,
            body=colorized_body if body is not None else '')
        return to_print

    def error(self, text):
        """Make error text red.

        Args:
            text (str): Text to color red.
        """
        return '{red}{text}{reset}'.format(
            red=self.red, text=text, reset=self.reset)

    def make_bold(self, text):
        """Make text bold.

        Args:
            text (str): Text to make bold.
        """
        return '{bold}{text}{reset}'.format(
            bold=self.bold, text=text, reset=self.reset)

    def colorize_response_code(self, status_code):
        """Color an HTTP response status code.

        Args:
            status_code (int): HTTP status code to color.
                4xx -> red
                2xx -> green
                other -> bold
        """
        if str(status_code).startswith('4'):
            color = self.red
        elif str(status_code).startswith('2'):
            color = self.green
        else:
            color = self.bold
        return '{color}{status_code}{reset}'.format(
            color=color, status_code=status_code, reset=self.reset)

if __name__ == '__main__':
    COLOR = Color()
    for color_name, number in COLOR.color_number.items():
        print(u'{color}  {block}{bold}{block}{color}' \
        ' {label} {bold}(bold){reset}'.format(
            color=COLOR.get_color_code(color_name),
            bold=COLOR.bold,
            label=color_name,
            block=u'\u2588' * 2,
            reset=COLOR.reset))
    print()
    print(COLOR.colorize_celery_script('kind', '{}'))
    print(COLOR.colorize_response_code(200))
    print(COLOR.colorize_response_code(300))
    print(COLOR.colorize_response_code(400))
    print(COLOR.make_bold('bold'))
    print(COLOR.error('ERROR'))
    print(COLOR.green + 'OK' + COLOR.reset)
