import sublime_plugin
import webbrowser
import subprocess
import threading
import sublime
import sys
import re
import os.path

from os import listdir, path
from sublime import Region

CORE = [
    'assert',  'buffer',  'child_process',  'cluster',  'crypto',  'dgram',
    'dns', 'domain',  'events',  'fs',  'http',  'https',  'net',  'os',  'path',
    'punycode',  'querystring',  'readline',  'stream',  'string_decoder',  'tls',
    'tty',  'url',  'util',  'v8',  'vm',  'zlib'
]

MODULE = r'.*(?:import.*?from.*?|require\()[\"\']([^.][^\.]*?)[\"\']\)?.*'
ICON = "Packages/npm-install/icon-%s.png"
data = {}
root = {}


def is_valid(view):
    return view.file_name() != None and view.file_name().endswith('.js')

def exec(args, pn):
    if sys.platform != 'win32':
        args = [ " ".join(args) ]
    return subprocess.Popen(args, cwd=pn, shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

def node_modules_ls(file, pn):
    if file not in root:       
        out, err = exec(['npm', 'root'], pn).communicate()
        out = out.decode().strip()
        root[file] = out
    try:
        ls = listdir(root[file])
        if len(ls):
            project = root[file].split('node_modules')[0]
            if not os.path.isfile('%spackage.json' % project):
              exec(['npm', 'init', '-f'], project).wait()
        return ls
    except Exception:
        return []


def cwd(view):
    project = re.match(r'(.*)[\/\\].*', view.file_name())
    return project.group(1)


def update_icons(view):

    file = view.file_name()

    modules = []
    installed = []
    other = []
    result = []

    if file not in data:
        view.run_command('npm_install', {'action': 'initial'})
    else:
        modules = data[file]
    
    for region in view.find_all(MODULE):
        m = re.search(MODULE, view.substr(region))
        a, b = m.span(1)
        module = m.group(1)
        reg = Region(a + region.begin(), b + region.begin())
        if module in modules or module in CORE:
            installed.append(reg)
        else:
            other.append(reg)
            result.append(module)

    flags = sublime.HIDE_ON_MINIMAP | sublime.DRAW_NO_FILL | sublime.DRAW_NO_OUTLINE | sublime.DRAW_SOLID_UNDERLINE
    view.add_regions('require-on', installed, 'request', ICON % 'on', flags)
    view.add_regions('require-off', other, 'request', ICON % 'off', flags)

    return result


def line(view):
    sel = view.sel()[0]
    line = view.full_line(sel)
    req = view.substr(line)
    match = re.match(MODULE, req)
    return (line, match.group(1) if match else None)


class NpmExec(threading.Thread):

    def __init__(self, module, root, action, view):
        self.module = module
        self.root = root
        self.action = action
        self.view = view
        self.mng = view.settings().get('npm_install_manager', 'npm')
        if self.mng == 'yarn':
            self.action = 'add' if action == 'install' else 'remove'
        threading.Thread.__init__(self)

    def run(self):
        if self.module not in CORE:

            args = [self.mng, self.action, self.module, '-s']

            if sys.platform != 'win32':
                args = [ " ".join(args) ]

            self.view.window().status_message('%sing %s' % (self.action, self.module))
            subprocess.Popen(args, shell=True, cwd=self.root).wait()
            self.view.run_command('npm_install', {'action': 'initial'})


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

        if self.action in ['install', 'initial']:
            root = cwd(self.view)
            file = self.view.file_name()
            data[file] = node_modules_ls(file, root)

        install = update_icons(self.view)

        if self.action is 'install':
            for module in install:
                NpmExec(module, root, 'install', self.view).start()


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


def initial(view):
    view.run_command('npm_install', {'action': 'initial'})


class EventEditor(sublime_plugin.EventListener):

    def on_modified(self, view):
        view.run_command('npm_install', {'action': 'mark'})

    def on_load(self, view):
        initial(view)

    def on_post_save(self, view):
        if view.settings().get('npm_install_on_save', True):
            view.run_command('npm_install')

    def get_module(self, module):
        clean = module.replace('-', '_').replace('@', '')
        return [module+'\tnpm', 'var %s = require(\'%s\');\n' % (clean, module)]

    def on_query_completions(self, view, prefix, locations):
        if is_valid(view) and view.settings().get('npm_autocomplete', True):
            file = view.file_name()
            if file in data:
                return [self.get_module(module) for module in data[file] if '.' not in module]
        return []


def plugin_loaded():
    for win in sublime.windows():
        for view in win.views():
            initial(view)
