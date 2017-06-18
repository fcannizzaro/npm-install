import sublime_plugin
import webbrowser as browser
from sublime import Region
import threading
import sublime
import re
from . import npm

NPMJS = 'https://www.npmjs.com/package/'

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
    match = re.match(npm.module_regex, req)
    if match: browser.open(NPMJS + match.group(1))
 
class NpmInstallCommand(sublime_plugin.TextCommand):

    def is_visible(self):
        return npm.is_valid(self.view)

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

      if not npm.is_valid(self.view):
        return

      # mark line as npm module
      regions = npm.icons(self.view)

      if not len(regions):
        return

      # list npm modules
      project = re.match(r'(.*)[\/\\].*', self.view.file_name())
      cwd = project.group(1)
      modules = npm.modules(cwd)
      
      # find modules and install/uninstall
      for region in regions:
        
        match = re.match(npm.module_regex, self.view.substr(region))
        module = match.group(1)
        
        if module[0] == '-':
           npm.uninstall(module[1:], self.view, cwd, region)           

        elif module not in modules:
          npm.install(module, self.view, cwd)

class EventEditor(sublime_plugin.EventListener):

    def on_modified_async(self, view):
        npm.icons(view)
        
    def on_activated_async(self, view):
        npm.icons(view)

    def on_post_save_async(self, view):
        if install_on_save:
            view.run_command('npm_install')
