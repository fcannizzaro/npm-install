import sublime_plugin
from . import npm
from . import settings

class NpmInstallCommand(sublime_plugin.TextCommand):

    def is_visible(self):
        return npm.is_valid(self.view)

    def run(self, edit):

      if not npm.is_valid(self.view) or not len(self.view.find_all(module_regex)):
        return

      # mark line as npm module
      npm.icons(self.view)

      # list npm modules
      project = re.match(r'(.*)[\/\\].*', self.view.file_name())
      cwd = project.group(1)
      modules = npm.modules(cwd)

      # parse file          
      content = self.view.substr(sublime.Region(0, self.view.size()))

      for module in re.findall(module_regex, content):
        if module[0] == '-':
           npm.uninstall(module[1:], self.view.window(), cwd)
        elif module not in modules:
          npm.install(module, self.view.window(), cwd)

class EventEditor(sublime_plugin.EventListener):

    def on_modified_async(self, view):
        npm.icons(view)
        
    def on_activated_async(self, view):
        npm.icons(view)

    def on_post_save_async(self, view):
        if install_on_save:
            view.run_command("npm_install")
