import sublime_plugin
import webbrowser as browser
from os import listdir, path
from sublime import Region
import subprocess
import threading
import sublime
import re

MODULE = r'.*require\(["\']([^.][^\.]*?)["\']\).*'
ICON = "Packages/npm-install/icon-%s.png"
data = {}
root = {}

settings = sublime.load_settings('npm-install.sublime-settings')
install_on_save = settings.get('install_on_save')

def is_valid(view):
  return view.file_name() != None and view.file_name().endswith('.js')

def npmls(file, p):
  if file not in root:
    out = subprocess.check_output(['npm', 'root'], cwd=p, shell=True)
    out = out.decode().strip()
    root[file] = out
  try:      
    return listdir(root[file])
  except Exception:
    return []

def cwd(view):
  project = re.match(r'(.*)[\/\\].*', view.file_name())
  return project.group(1)

def update_icons(view):

    file = view.file_name()
    
    if file not in data: 
      view.run_command('npm_install', {'action':'initial'})
      return

    installed = []    
    other = []
    result = []

    for region in view.find_all(MODULE):
      m = re.search(MODULE, view.substr(region))
      a,b = m.span(1)
      module = m.group(1)
      reg = Region(a + region.begin(), b + region.begin())
      if module in data[file]:
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
        threading.Thread.__init__(self)

    def run(self):      
      self.view.window().status_message('%sing %s' % (self.action, self.module))
      subprocess.Popen(['npm', self.action, self.module, '-s'], shell=True, cwd=self.root).wait()
      self.view.run_command('npm_install', {'action':'initial'}) 
  
class NpmDocCommand(sublime_plugin.TextCommand):

  def run(self, edit):
    region, module = line(self.view)
    if module: browser.open('https://www.npmjs.com/package/' + module)
 
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
        data[file] = npmls(file, root)

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

class EventEditor(sublime_plugin.EventListener):

  def on_modified(self, view):
    view.run_command('npm_install', {'action':'mark'}) 
        
  def on_load(self, view):
    view.run_command('npm_install', {'action':'initial'})

  def on_post_save(self, view):
    if install_on_save:
      view.run_command('npm_install')

def plugin_loaded():
  for win in sublime.windows():
    for view in win.views():
      view.run_command('npm_install', {'action':'initial'})

