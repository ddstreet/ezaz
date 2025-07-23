
import cmd

from functools import partialmethod


class YesNoCmd(cmd.Cmd):
    def __init__(self, prompt, default_yes=False):
        super().__init__(completekey=None)
        self.prompt = f'{prompt} ({"Y/n" if default_yes else "y/N"}) '
        self.yes = default_yes
        self.cmdloop()

    def precmd(self, line):
        return line.lower()

    def postcmd(self, stop, line):
        return True

    def do_y(self, arg):
        self.yes = True

    def do_yes(self, arg):
        self.yes = True

    def do_n(self, arg):
        self.yes = False

    def do_no(self, arg):
        self.yes = False

    def default(self, line):
        pass


def YesNo(prompt, default=False):
    return YesNoCmd(prompt, default=default).yes


def AzObjectChoice(azobject_class, azobject_choices, azobject_default):
    azobject_text = azobject_class.azobject_text()
    default_id = azobject_default.azobject_id if azobject_default else None

    intro = f'Available {azobject_text}:\n'
    for azobject in azobject_choices:
        azobject_id = azobject.azobject_id
        intro += '  ' + azobject_id
        if azobject_id == default_id:
            intro += ' (default)'
        intro += '\n'

    class AzObjectChoiceCmd(cmd.Cmd):
        def __init__(self):
            super().__init__()
            self.prompt = f'Please select a {azobject_text}: '
            self.choice = azobject_default
            self.cmdloop(intro)

        def set_choice(self, choice, arg):
            self.choice = choice
            return True

        def emptyline(self):
            if self.choice:
                return True
            return super().emptyline()

    for azobject in azobject_choices:
        azobject_id = azobject.azobject_id
        setattr(AzObjectChoiceCmd, f'do_{azobject_id}', partialmethod(AzObjectChoiceCmd.set_choice, azobject))

    return AzObjectChoiceCmd().choice
