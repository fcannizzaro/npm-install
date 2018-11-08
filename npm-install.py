import re
import subprocess
import sys
import threading
import webbrowser

import sublime
import sublime_plugin
from sublime import Region

package_settings = sublime.load_settings('NpmInstall.sublime-settings')

MODULE = r'.*(?:import.*?from.*?|require\()[\"\'](.+[^\"\'\/\n]*)?[\"\']\)?.*'
ICON = "Packages/npm-install/icon-%s.png"
data, prev, root, progress = {}, {}, {}, {}


def get_settings(view, key, default):
    return view.settings().get(key, default) or package_settings.get(key[5:], default)


def clear_args(args):
    return [' '.join(args)] if sys.platform != 'win32' else args


def exec_command(args, pn=None):
    return subprocess.Popen(
        clear_args(args),
        cwd=pn,
        shell=True,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT
    )


def init_core_modules():
    out, err = exec_command(['node', '-pe', 'require(\'repl\')._builtinLibs.join(\',\')']).communicate()
    return out.decode().strip().split(',')


CORE = init_core_modules()


def is_valid(view):
    return view.file_name() and view.file_name().endswith('.js')


# noinspection PyBroadException
def node_modules_ls(file, pn):
    if file not in root:
        out, err = exec_command(['npm', 'root'], pn).communicate()
        out = out.decode().strip()
        root[file] = out

    out, err = exec_command(['npm', 'ls', '--parseable', '--depth=0'], root[file]).communicate()
    items = out.decode().split('\n')
    return [item.replace('\\', '/').split('node_modules/')[1] for item in items if 'node_modules' in item]


def cwd(view):
    project = re.match(r'(.*)[/\\].*', view.file_name())
    return project.group(1)


def update_icons(view):
    file = view.file_name()
    modules, installed, other, result, all_modules = [], [], [], [], []

    if file not in data:
        view.run_command('npm_install', {'action': 'initial'})
    else:
        modules = data[file]

    for region in view.find_all(MODULE):
        m = re.search(MODULE, view.substr(region))
        a, b = m.span(1)
        module = m.group(1)
        reg = Region(a + region.begin(), b + region.begin())
        all_modules.append(module)
        if module in modules or module in CORE:
            installed.append(reg)
        else:
            other.append(reg)
            result.append(module)

    flags = sublime.HIDE_ON_MINIMAP | sublime.DRAW_NO_FILL | sublime.DRAW_NO_OUTLINE | sublime.DRAW_SOLID_UNDERLINE
    view.add_regions('require-on', installed, 'request', ICON % 'on', flags)
    view.add_regions('require-off', other, 'request', ICON % 'off', flags)

    return result, all_modules


def line(view):
    sel = view.sel()[0]
    single_line = view.full_line(sel)
    req = view.substr(single_line)
    match = re.match(MODULE, req)
    return single_line, match.group(1) if match else None


class NpmExec(threading.Thread):

    def __init__(self, module, _root, action, view):
        self.module = module
        self.root = _root
        self.action = action
        self.view = view
        self.mng = get_settings(view, 'npm_install_manager', 'npm')
        if self.mng == 'yarn':
            self.action = 'add' if action == 'install' else 'remove'
        threading.Thread.__init__(self)

    def run(self):

        if self.module not in CORE and self.module not in progress:

            args = [self.mng, self.action, self.module, '-s']
            progress[self.module] = True
            self.view.window().status_message('%sing %s' % (self.action, self.module))

            subprocess.Popen(clear_args(args), shell=True, cwd=self.root).wait()
            progress.pop(self.module, None)
            initial(self.view)

            if self.action in ['uninstall', 'remove'] and get_settings(self.view, 'npm_prune_on_uninstall', False):
                subprocess.Popen(clear_args([self.mng, 'prune']), shell=True, cwd=self.root).wait()


class NpmDocCommand(sublime_plugin.TextCommand):

    def is_visible(self):
        region, module = line(self.view)
        return not not module

    def run(self, edit):
        region, module = line(self.view)
        if module:
            webbrowser.open('https://www.npmjs.com/package/' + module)


class NpmCommand(threading.Thread):

    def __init__(self, view, edit, action):
        self.view = view
        self.edit = edit
        self.action = action
        threading.Thread.__init__(self)

    def run(self):

        if self.action == 'mark':
            update_icons(self.view)

        elif self.action in ['install', 'initial']:
            cwd_root = cwd(self.view)
            file = self.view.file_name()
            data[file] = node_modules_ls(file, cwd_root)
            install, all_modules = update_icons(self.view)

            for module in set(prev[file] if file in prev else []) - set(all_modules):
                NpmExec(module, cwd(self.view), 'uninstall', self.view).start()

            prev[file] = all_modules

            if self.action is 'install':
                for module in install:
                    NpmExec(module, cwd_root, 'install', self.view).start()


class NpmInstallCommand(sublime_plugin.TextCommand):

    def is_visible(self):
        return is_valid(self.view)

    def run(self, edit, action='install'):
        if is_valid(self.view):
            NpmCommand(self.view, edit, action).start()


class NpmUninstallCommand(sublime_plugin.TextCommand):

    def is_visible(self):
        region, module = line(self.view)
        return not not module

    def run(self, edit):
        if is_valid(self.view):
            region, module = line(self.view)
            reply = sublime.yes_no_cancel_dialog('Remove "%s" module?' % module, 'Yes', 'No')
            if reply == 1:
                self.view.erase(edit, region)
                NpmExec(module, cwd(self.view), 'uninstall', self.view).start()


def clear_file(view):
    file = view.file_name()
    data.pop(file, None)
    prev.pop(file, None)
    root.pop(file, None)


def initial(view):
    view.run_command('npm_install', {'action': 'initial'})


# noinspection PyMethodMayBeStatic
class EventEditor(sublime_plugin.EventListener):

    def on_modified(self, view):
        view.run_command('npm_install', {'action': 'mark'})

    def on_load(self, view):
        initial(view)

    def on_close(self, view):
        clear_file(view)

    def on_post_save(self, view):
        if get_settings(view, 'npm_install_on_save', True):
            view.run_command('npm_install')

    def get_module(self, module):
        clean = module.replace('-', '_').replace('@', '')
        return [module + '\tnpm', 'var %s = require(\'%s\');\n' % (clean, module)]

    # noinspection PyUnusedLocal
    def on_query_completions(self, view, prefix, locations):
        if is_valid(view) and get_settings(view, 'npm_autocomplete', False):
            file = view.file_name()
            if file in data:
                return [self.get_module(module) for module in data[file] if '.' not in module]
        return []


def plugin_loaded():
    for win in sublime.windows():
        for view in win.views():
            initial(view)
