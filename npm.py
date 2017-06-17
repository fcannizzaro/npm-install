import subprocess
import threading
import sublime
import re

module_regex = r'.*require\(["\']([^.].*?)["\']\).*'

def icons(view):
  regions = view.find_all(module_regex)
  flags = sublime.HIDE_ON_MINIMAP | sublime.DRAW_NO_FILL | sublime.DRAW_NO_OUTLINE
  view.add_regions('require', regions, 'npm', 'Packages/npm-install/icon.png', flags)

def is_valid(view):
  return '.js' in view.file_name()

def modules(root):
  modules = []
  p = subprocess.Popen(['npm', 'ls', '-parseable', '-depth=0'], shell=True, cwd=root, stdout=subprocess.PIPE)
  next(p.stdout)
  for line in p.stdout:
    m = re.match(r'.*(?:\\\\|/)(.*)\\.*', str(line))
    if m:
      modules.append(m.group(1))
  return modules

def install(module, window, root):
  Exec(module,window, root, 'install').start()

def uninstall(module, window, root):
  Exec(module,window, root, 'uninstall').start()

class Exec(threading.Thread):

    def __init__(self, module, window, root, action):
        self.module = module
        self.window = window
        self.root = root
        self.action = action
        threading.Thread.__init__(self)

    def run(self):
      self.window.status_message('%sing %s' % (self.action, self.module))
      subprocess.Popen(['npm', self.action, self.module, '-s'], shell=True, cwd=self.root)
      print('npm', self.action, self.module)
