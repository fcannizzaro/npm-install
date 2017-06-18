import subprocess
import threading
import sublime
import re

module_regex = r'.*require\(["\']([^.].*?)["\']\).*'

def icons(view):
  regions = view.find_all(module_regex)
  modules = []

  for region in regions:
    text = view.substr(region)
    m = re.search(module_regex, text)
    a,b = m.span(1)
    if m.group(1)[0] != '-':
      modules.append(sublime.Region(a + region.begin(),b + region.begin()))

  flags = sublime.HIDE_ON_MINIMAP | sublime.DRAW_NO_FILL | sublime.DRAW_NO_OUTLINE
  view.add_regions('require', regions, 'npm', 'Packages/npm-install/icon.png', flags)

  flags |= sublime.DRAW_SOLID_UNDERLINE
  view.add_regions('modules', modules, 'modules', flags=flags)

  return regions

def is_valid(view):
  return view.file_name().endswith('.js')

def modules(root):
  modules = []
  p = subprocess.Popen(['npm', 'ls', '-parseable', '-depth=0'], shell=True, cwd=root, stdout=subprocess.PIPE)
  next(p.stdout)
  for line in p.stdout:
    m = re.match(r'.*(?:\\\\|/)(.*)\\.*', str(line))
    if m:
      modules.append(m.group(1))
  return modules

def install(module, view, root):
  Exec(module, view.window(), root, 'install').start()

def uninstall(module, view, root, region):
  Exec(module, view.window(), root, 'uninstall', region, view).start()

class Exec(threading.Thread):

    def __init__(self, module, window, root, action, region=None, view=None):
        self.module = module
        self.window = window
        self.root = root
        self.action = action
        self.region = region
        self.view = view
        threading.Thread.__init__(self)

    def run(self):
      self.window.status_message('%sing %s' % (self.action, self.module))
      subprocess.Popen(['npm', self.action, self.module, '-s'], shell=True, cwd=self.root)
      print('npm', self.action, self.module)
      if self.view:
        self.view.run_command("npm_clear", { 'a': self.region.a, 'b': self.region.b })

