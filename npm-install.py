import sublime_plugin
import webbrowser as browser
from sublime import Region
import subprocess
import threading
import sublime
import re

module_regex = r'.*require\(["\']([^.].*?)["\']\).*'
NPMJS = 'https://www.npmjs.com/package/'

def icons(view):
  regions = view.find_all(module_regex)
  modules = []

  for region in regions:
    text = view.substr(region)
    m = re.search(module_regex, text)
    a,b = m.span(1)
    if m.group(1)[0] != '-':
      modules.append(Region(a + region.begin(),b + region.begin()))

  flags = sublime.HIDE_ON_MINIMAP | sublime.DRAW_NO_FILL | sublime.DRAW_NO_OUTLINE
  view.add_regions('require', regions, 'npm', 'Packages/npm-install/icon.png', flags)

  flags |= sublime.DRAW_SOLID_UNDERLINE
  view.add_regions('modules', modules, 'modules', flags=flags)

  return regions

def is_valid(view):
  return view.file_name().endswith('.js')

def find_modules(root):
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

def update_settings():
  install_on_save = settings.get('install_on_save')

install_on_save = True
settings = sublime.load_settings('npm-install.sublime-settings')
settings.add_on_change('install_on_save', update_settings)
update_settings()

class NpmDocCommand(sublime_plugin.TextCommand):

  def run(self, edit):
    sel = self.view.sel()[0]
    line = self.view.full_line(sel)
    req = self.view.substr(line)
    match = re.match(module_regex, req)
    if match: browser.open(NPMJS + match.group(1))
 
class NpmInstallCommand(sublime_plugin.TextCommand):

    def is_visible(self):
        return is_valid(self.view)

    def run(self, edit):
      Command(self.view, edit).start()
 
class NpmClearCommand(sublime_plugin.TextCommand):

    def run(self, edit, a, b):
      self.view.erase(edit, Region(a,b))

class Command(threading.Thread):

    def __init__(self, view, edit):
        self.view = view
        self.edit = edit
        threading.Thread.__init__(self)

    def run(self):

      if not is_valid(self.view):
        return

      # mark line as npm module
      regions = icons(self.view)

      if not len(regions):
        return

      # list npm modules
      project = re.match(r'(.*)[\/\\].*', self.view.file_name())
      cwd = project.group(1)
      modules = find_modules(cwd)
      
      # find modules and install/uninstall
      for region in regions:
        
        match = re.match(module_regex, self.view.substr(region))
        module = match.group(1)
        
        if module[0] == '-':
           uninstall(module[1:], self.view, cwd, region)           

        elif module not in modules:
          install(module, self.view, cwd)

class EventEditor(sublime_plugin.EventListener):

    def on_modified_async(self, view):
        icons(view)
        
    def on_activated_async(self, view):
        icons(view)

    def on_post_save_async(self, view):
        if install_on_save:
            view.run_command('npm_install')
