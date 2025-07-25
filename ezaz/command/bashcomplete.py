
import os
import re

from pathlib import Path

from .command import ActionCommand


class BashCompletionCommand(ActionCommand):
    @classmethod
    def command_name_list(cls):
        return ['bash', 'completion']

    @classmethod
    def parser_add_action_arguments(cls, group):
        super().parser_add_action_arguments(group)
        cls._parser_add_action_argument(group, '--show',
                                        help=f'Show if bash-completion is enabled')
        cls._parser_add_action_argument(group, '-e', '--enable',
                                        help=f'Enable bash-completion for ezaz (default)')
        cls._parser_add_action_argument(group, '-d', '--disable',
                                        help=f'Disable bash-completion for ezaz')

    @classmethod
    def parser_set_action_default(cls, group):
        cls._parser_set_action_default(group, 'show')

    def check_bash_completion(self):
        profile_bash_completion = Path('/etc/profile.d/bash_completion.sh')
        if not profile_bash_completion.is_file():
            print('Script {profile_bash_completion} is missing; continuing anyway, but you may need to install the bash-completion package')

    @property
    def user_bash_completion_path(self):
        # This is the standard location for user bash completion when the bash-completion package is installed (except for Photon-based distros)
        return Path(os.environ.get('XDG_CONFIG_HOME', '~/.config')).expanduser() / 'bash_completion'

    @property
    def idtag(self):
        return 'Added by ezaz'

    @property
    def idwarning(self):
        return 'DO NOT EDIT, instead use: ezaz bashcompletion -d'

    @property
    def register_python_argcomplete_path(self):
        # This expects the venv to have argcomplete installed
        return self._venv.bindir / 'register-python-argcomplete'

    @property
    def register_ezaz_line(self):
        register = self.register_python_argcomplete_path
        return f'[[ -f {register} ]] && eval "$({register} ezaz)"  # {self.idtag}, {self.idwarning}\n'

    @property
    def active_pattern(self):
        return rf'(?m)^(?P<space>\s*)(?P<line>[^\s#].*{self.idtag}.*)$'

    @property
    def inactive_pattern(self):
        return rf'(?m)^(?P<space>\s*)#(?P<line>.*{self.idtag}.*)$'

    def check_user_bash_completion_path(self):
        if not self.user_bash_completion_path.is_file():
            print('No custom bash completion is currently enabled')
            return False
        return True

    def print_bash_completion(self, msg):
        if msg:
            print(msg)
        if self.verbose and self.user_bash_completion_path.is_file():
            print(f'{self.user_bash_completion_path}:\n{self.user_bash_completion_path.read_text()}')

    def show(self):
        self.check_bash_completion()

        if not self.check_user_bash_completion_path():
            return

        text = self.user_bash_completion_path.read_text()
        enabled = 'enabled' if re.search(self.active_pattern, text) else 'not enabled'
        self.print_bash_completion(f'Bash completion for ezaz is {enabled}')

    def enable(self):
        self.check_bash_completion()

        if self.user_bash_completion_path.is_file():
            text = self.user_bash_completion_path.read_text()
            if re.search(self.active_pattern, text):
                self.print_bash_completion(f'Bash completion already enabled for ezaz')
                return
            if re.search(self.inactive_pattern, text):
                text = re.sub(self.inactive_pattern, r'\g<space>\g<line>', text)
            else:
                text += self.register_ezaz_line
        else:
            text = self.register_ezaz_line

        self.user_bash_completion_path.write_text(text)
        self.print_bash_completion(f'Enabled bash completion for ezaz, please relogin (or bash --login)')

    def disable(self):
        if not self.check_user_bash_completion_path():
            return

        text = self.user_bash_completion_path.read_text()
        if not re.search(self.active_pattern, text):
            self.print_bash_completion('Bash completion already disabled for ezaz')
            return
        text = re.sub(self.active_pattern, r'\g<space>#\g<line>', text)

        self.user_bash_completion_path.write_text(text)
        self.print_bash_completion(f"Disabled bash completion for ezaz")
