"""
SublimeUberSettings
https://github.com/mariusz-kowalski/SublimeUberSettings
Copyright (c) 2017-2022 Toby Giacometti and contributors
Apache License 2.0
"""

import json
import os

import sublime  # pylint: disable=import-error
import sublime_plugin  # pylint: disable=import-error


configured_views = []  # pylint: disable=invalid-name


def plugin_loaded():
    """https://www.sublimetext.com/docs/3/api_reference.html"""
    for window in sublime.windows():
        for view in window.views():
            apply_settings(view)


def parent_dir(path):
    """
    :param str path: Path for which the parent directory should be retrieved.
    :return: Parent directory path. An empty string is returned if the provided path is the root directory.
    :rtype: str
    """
    parent_path = os.path.abspath(os.path.join(path, os.pardir))
    if parent_path == path:
        return ""
    return parent_path


def file_settings(file):
    """
    :param str file: Path of a file that contains settings.
    :return: Settings that are stored in the provided file. If the file cannot be found or an error occurs, an empty dictionary is returned.
    :rtype: dict
    """
    if not os.path.isfile(file):
        return {}
    print("SublimeUberSettings: loading settings from " + file)
    with open(file, encoding="utf-8") as file_object:
        try:
            # Użyj sublime.decode_value zamiast json.load
            content = file_object.read()
            return sublime.decode_value(content)
        except Exception as exception:  # Używamy Exception, bo decode_value może rzucić różne błędy
            print(
                "SublimeUberSettings: error loading settings from "
                + file
                + ": "
                + repr(exception)
            )
            return {}

def view_settings(view):
    """Retrieve settings that should be applied to a Sublime Text view."""
    settings = {}
    syntax_file = view.settings().get("syntax")
    syntax_name = os.path.splitext(os.path.basename(syntax_file))[0]
    settings_dir = parent_dir(view.file_name())
    while True:
        settings_files = [
            settings_dir + "/" + syntax_name + ".sublime-settings",
            settings_dir + "/Preferences.sublime-settings",
        ]
        for settings_file in settings_files:
            dir_settings = file_settings(settings_file)
            dir_settings.update(settings)
            settings = dir_settings
        settings_dir = parent_dir(settings_dir)
        if not settings_dir:
            break
    return settings


def apply_settings(view):
    """
    :param sublime.View view: Sublime Text view to which settings should be applied.
    """
    if view.id() in configured_views:
        return
    for name, value in view_settings(view).items():
        view.settings().set(name, value)
    configured_views.append(view.id())


class SublimeUberSettingsListener(sublime_plugin.EventListener):
    """https://www.sublimetext.com/docs/3/api_reference.html"""
    def on_load(self, view):
        apply_settings(view)

    def on_post_save(self, view):
        apply_settings(view)

    def on_close(self, view):
        try:
            configured_views.remove(view.id())
        except ValueError:
            pass


class CreateUberSettingsCommand(sublime_plugin.WindowCommand):
    """Command to create a new settings file in the current project directory."""
    def run(self):
        view = self.window.active_view()
        if not view or not view.file_name():
            sublime.error_message("No file is currently open!")
            return

        project_dir = parent_dir(view.file_name())
        if not project_dir:
            sublime.error_message("Could not determine project directory!")
            return

        settings_file = os.path.join(project_dir, "Preferences.sublime-settings")

        if os.path.exists(settings_file):
            sublime.message_dialog("Settings file already exists at: {}".format(settings_file))
            return

        # Pobierz ścieżkę do globalnych ustawień użytkownika
        user_settings_path = os.path.join(sublime.packages_path(), "User", "Preferences.sublime-settings")
        
        # Sprawdź, czy plik użytkownika istnieje
        if os.path.exists(user_settings_path):
            try:
                # Skopiuj plik bezpośrednio, bez parsowania
                with open(user_settings_path, "r", encoding="utf-8") as source:
                    with open(settings_file, "w", encoding="utf-8") as target:
                        target.write(source.read())
                sublime.message_dialog("Created settings file at: {}".format(settings_file))
                self.window.open_file(settings_file)
            except Exception as e:
                sublime.error_message("Error copying settings file: {}".format(str(e)))
        else:
            # Jeśli plik użytkownika nie istnieje, utwórz domyślny
            default_settings = {
                "font_size": 12,
                "tab_size": 4,
                "translate_tabs_to_spaces": True
            }
            try:
                with open(settings_file, "w", encoding="utf-8") as f:
                    # Zapisz domyślne ustawienia jako JSON z komentarzem przykładowym
                    f.write("// Default settings copied by SublimeUberSettings\n")
                    f.write(json.dumps(default_settings, indent=4))
                sublime.message_dialog("Created default settings file at: {}".format(settings_file))
                self.window.open_file(settings_file)
            except Exception as e:
                sublime.error_message("Error creating settings file: {}".format(str(e)))