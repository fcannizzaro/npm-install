# `npm-install` for sublime text 3
auto install npm modules, show npm icons, autocomplete require, open npmjs documentation.

![preview](https://raw.githubusercontent.com/fcannizzaro/npm-install/master/npm-install.png)

|           Command           | Default shortcut key<br>(Windows, Linux) | Default shortcut key<br>(OS X) | Extra
|---------------------------|-------------------------------------|---------------------------|---------------------------|
|Install Modules |<kbd>CTRL</kbd>+<kbd>ALT</kbd>+<kbd>I</kbd>|<kbd>⌘</kbd>+<kbd>option</kbd>+<kbd>I</kbd>| Command Palette
|Uninstall Module|<kbd>CTRL</kbd>+<kbd>ALT</kbd>+<kbd>U</kbd><br><kbd>ALT</kbd>+<kbd>RIGHT CLICK</kbd>|<kbd>⌘</kbd>+<kbd>option</kbd>+<kbd>U</kbd><br><kbd>option</kbd>+<kbd>RIGHT CLICK</kbd>| Command Palette<br>Context Menu
|Open Documentation on [npmjs](https://www.npmjs.com)|<kbd>ALT</kbd>+<kbd>ENTER</kbd><br><kbd>ALT</kbd>+<kbd>CLICK</kbd>|<kbd>option</kbd>+<kbd>ENTER</kbd><br><kbd>option</kbd>+<kbd>CLICK</kbd>| Command Palette<br>Context Menu

## Icons
| Icon |    Description   |
|:----:|:----------------:|
| ![on](https://raw.githubusercontent.com/fcannizzaro/npm-install/master/icon-on.png)   | installed module |
| ![off](https://raw.githubusercontent.com/fcannizzaro/npm-install/master/icon-off.png) |  missing module  |

## Settings

|         key           |    default    |                        action                     |
|-----------------------|:-------------:|---------------------------------------------------|
| `npm_autocomplete`    |   **true**    | autocomplete node modules's require.              |
| `npm_install_on_save` |   **true**    | auto-install node modules **on save**.            |
| `npm_install_manager` |   **"npm"**   | javascript package manager: `npm`, `yarn`, `pnpm` |
