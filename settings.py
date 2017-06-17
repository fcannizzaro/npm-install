import sublime

def update_settings():
  install_on_save = settings.get('install_on_save')

install_on_save = True
settings = sublime.load_settings('npm-install.sublime-settings')
settings.add_on_change('install_on_save', update_settings)
update_settings()
