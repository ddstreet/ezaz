
import cmd

from contextlib import suppress
from functools import partialmethod

from .exception import NoChoiceError


def YesNo(prompt, default=False):
    class YesNoCmd(cmd.Cmd):
        def __init__(self):
            super().__init__(completekey=None)
            yn = 'y/n' if default is None else 'Y/n' if default else 'y/N'
            self.prompt = f'{prompt} ({yn}) '
            self.yes = default
            self.cmdloop()

        def precmd(self, line):
            return line.lower()

        def do_y(self, arg):
            self.yes = True
            return True

        def do_yes(self, arg):
            self.yes = True
            return True

        def do_n(self, arg):
            self.yes = False
            return True

        def do_no(self, arg):
            self.yes = False
            return True

        def default(self, line):
            print('Please respond y or n')

        def emptyline(self):
            return self.default('') if self.yes is None else True

    return YesNoCmd().yes


def Choice(choices, default=None,
           intro_text='Choices available',
           prompt_text='Please select a choice',
           emptyline_text='There is no default, please respond with one of the choices',
           invalid_text='Please respond with one of the choices',
           choice_text_fn=lambda c: c,
           choice_hint_fn=None,
           choice_cmp_fn=lambda a, b: a == b):

    if not choices:
        raise NoChoiceError('There are no choices')

    class ChoiceCmd(cmd.Cmd):
        def __init__(self, intro, choicemap):
            super().__init__()
            self.prompt = f'{prompt_text}: '
            self.choice = default
            self.choicemap = choicemap
            self.cmdloop(intro)

        def completenames(self, text, *ignored):
            return [c for c in self.choicemap.keys() if c.startswith(text)]

        def emptyline(self):
            if self.choice is not None:
                return True
            print(emptyline_text)

        def default(self, line):
            with suppress(KeyError):
                self.choice = self.choicemap[line]
                return True
            print(invalid_text)

    intro = f'{intro_text}:\n'
    for choice in choices:
        intro += f'  {choice_text_fn(choice)}'
        if choice_hint_fn:
            hint = choice_hint_fn(choice)
            if hint:
                intro += f' [{hint}]'
        if default is not None and choice_cmp_fn(choice, default):
            intro += ' (default)'
        intro += '\n'

    return ChoiceCmd(intro, {choice_text_fn(c): c for c in choices}).choice


# Use kwargs to provide the *_text params
def AzObjectChoice(azobject_choices, azobject_default,
                   text_fn=lambda o: o.azobject_id,
                   hint_fn=None,
                   cmp_fn=lambda a, b: a.azobject_id == b.azobject_id,
                   **kwargs):

    if not azobject_choices:
        raise NoChoiceError('There are no choices')

    kwargs.setdefault('prompt_text', f'Please select a {azobject_choices[0].azobject_text()}')

    return Choice(azobject_choices, default=azobject_default,
                  choice_text_fn=text_fn,
                  choice_hint_fn=hint_fn,
                  choice_cmp_fn=cmp_fn,
                  **kwargs)
