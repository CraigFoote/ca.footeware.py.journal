# window.py
#
# Copyright 2025 Craig Foote
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
# SPDX-License-Identifier: GPL-3.0-or-later

from gi.repository import Adw
from gi.repository import Gtk
from gi.repository import Gio
from gi.repository import GLib
import jprops
import collections
import os
import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')


@Gtk.Template(resource_path='/ca/footeware/py/journal/window.ui')
class JournalWindow(Adw.ApplicationWindow):
    __gtype_name__ = 'JournalWindow'

    calendar = Gtk.Template.Child()
    textview = Gtk.Template.Child()
    new_journal_location = Gtk.Template.Child()
    new_journal_name = Gtk.Template.Child()
    new_journal_password_1 = Gtk.Template.Child()
    new_journal_password_2 = Gtk.Template.Child()
    existing_journal_location = Gtk.Template.Child()
    existing_journal_password = Gtk.Template.Child()
    first_button = Gtk.Template.Child()
    previous_button = Gtk.Template.Child()
    today_button = Gtk.Template.Child()
    next_button = Gtk.Template.Child()
    last_button = Gtk.Template.Child()
    save_button = Gtk.Template.Child()
    toast_overlay = Gtk.Template.Child()
    window_title = Gtk.Template.Child()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # read UI file
        self.init_template()

        # 'New - Browse For Folder' action
        new_browse_for_folder_action = Gio.SimpleAction.new("new_browse_for_folder", None)
        new_browse_for_folder_action.connect("activate", self.on_new_browse_for_folder_action)
        self.add_action(new_browse_for_folder_action)

        # 'Create Journal' action
        create_journal_action = Gio.SimpleAction.new("create_journal", None)
        create_journal_action.connect("activate", self.on_create_journal_action)
        self.add_action(create_journal_action)

        # 'Open - Browse for journal' action
        open_browse_for_journal_action = Gio.SimpleAction.new("open_browse_for_journal", None)
        open_browse_for_journal_action.connect("activate", self.on_open_browse_for_journal_action)
        self.add_action(open_browse_for_journal_action)

        # 'Open Journal' action
        open_journal_action = Gio.SimpleAction.new("open_journal", None)
        open_journal_action.connect("activate", self.on_open_journal_action)
        self.add_action(open_journal_action)

        # 'Save Journal' action
        save_journal_action = Gio.SimpleAction.new("save_journal", None)
        save_journal_action.connect("activate", self.on_save_journal_action)
        self.get_application().set_accels_for_action("win.save_journal", ['<control>s'])
        self.add_action(save_journal_action)

        # calendar listeners
        self.calendar.connect("day-selected", self.on_day_selected)
        self.calendar.connect("prev-month", self.on_prev_month)
        self.calendar.connect("next-month", self.on_next_month)
        self.calendar.connect("prev-year", self.on_prev_year)
        self.calendar.connect("next-year", self.on_next_year)

        # First action
        first_action = Gio.SimpleAction.new("first", None)
        first_action.connect("activate", self.on_first_action)
        self.add_action(first_action)

        # Previous action
        previous_action = Gio.SimpleAction.new("previous", None)
        previous_action.connect("activate", self.on_previous_action)
        self.add_action(previous_action)

        # Today action
        today_action = Gio.SimpleAction.new("today", None)
        today_action.connect("activate", self.on_today_action)
        self.add_action(today_action)

        # Previous action
        next_action = Gio.SimpleAction.new("next", None)
        next_action.connect("activate", self.on_next_action)
        self.add_action(next_action)

        # Last action
        last_action = Gio.SimpleAction.new("last", None)
        last_action.connect("activate", self.on_last_action)
        self.add_action(last_action)

        # textview
        self.buffer = self.textview.get_buffer()
        self.buffer.connect("changed", self.on_buffer_changed)

        # initialize variables
        self.properties = {}
        self.date = GLib.DateTime.new_now_local()


    def on_first_action(self, action, parameters=None):
        """Respond to the First button being clicked."""
        keys = self.get_sorted_keys()
        if len(keys) > 0:
            first = keys[0]
            year = first[:4]
            month = first[5:7]
            day = first[8:]
            date = GLib.DateTime.new_local(int(year), int(month), int(day), 0, 0, 0)
            self.calendar.select_day(date)
            self.mark_calendar_days()


    def on_previous_action(self, action, parameters=None):
        """Respond to the Previous button being clicked."""
        current_date = self.calendar.get_date()
        current_date_str = current_date.format('%Y-%m-%d')
        keys = self.get_sorted_keys()
        if len(keys) > 0:
            key = None
            if current_date_str in keys:
                index = keys.index(current_date_str)
                if index - 1 >= 0:
                    # display previous entry
                    key = keys[index - 1]
            else:
                # display last entry
                key = keys[len(keys) - 1]
            if key is not None:
                year = key[:4]
                month = key[5:7]
                day = key[8:]
                self.date = GLib.DateTime.new_local(int(year), int(month), int(day), 0, 0, 0)
                self.calendar.select_day(self.date)
                self.mark_calendar_days()


    def on_today_action(self, action, parameters=None):
        """Respond to request to navigate to 'today' in calendar."""
        self.calendar.select_day(GLib.DateTime.new_now_local())
        self.date = self.calendar.get_date();
        self.mark_calendar_days()


    def on_next_action(self, action, parameters=None):
        """Respond to the Next button being clicked."""
        current_date = self.calendar.get_date()
        current_date_str = current_date.format('%Y-%m-%d')
        keys = self.get_sorted_keys()
        if len(keys) > 0:
            key = None
            if current_date_str in keys:
                index = keys.index(current_date_str)
                if index + 1 <= len(keys) - 1:
                    # display next entry
                    key = keys[index + 1]
            else:
                # display first entry
                key = keys[0]
            if key is not None:
                year = key[:4]
                month = key[5:7]
                day = key[8:]
                self.date = GLib.DateTime.new_local(int(year), int(month), int(day), 0, 0, 0)
                self.calendar.select_day(self.date)
                self.mark_calendar_days()


    def on_last_action(self, action, parameters=None):
        """Respond to the Last button being clicked."""
        keys = self.get_sorted_keys()
        if len(keys) > 0:
            last = keys[len(keys) - 1]
            year = last[:4]
            month = last[5:7]
            day = last[8:]
            date = GLib.DateTime.new_local(int(year), int(month), int(day), 0, 0, 0)
            self.calendar.select_day(date)
            self.mark_calendar_days()


    def get_sorted_keys(self):
        """Return a sorted copy of the journal keys (dates)."""
        keys = []
        for key, value in self.properties.items():
            keys.append(key)
        keys.sort()
        return keys


    def on_prev_month(self, calendar):
        """Respond to pressing of Previous Month button."""
        self.date = calendar.get_date()
        self.mark_calendar_days();


    def on_next_month(self, calendar):
        """Respond to pressing of Next Month button."""
        self.date = calendar.get_date()
        self.mark_calendar_days();


    def on_prev_year(self, calendar):
        """Respond to pressing of Previous Year button."""
        self.date = calendar.get_date()
        self.mark_calendar_days();


    def on_next_year(self, calendar):
        """Respond to pressing of Next Year button."""
        self.date = calendar.get_date()
        self.mark_calendar_days();


    def on_day_selected(self, calendar):
        """React to a new day being selected in the calendar."""
        # store date from previous selection, we may need to save its entry
        self.old_date = self.date
        self.date = calendar.get_date()
        date_str = self.date.format('%Y-%m-%d')
        if self.window_title.get_title().startswith("• "):
            dialog = Adw.MessageDialog(
                transient_for=self,
                modal=True,
                heading="Save changes?",
            )
            file_name = os.path.basename(self.file_path)
            dialog.set_body(f'The editor has unsaved changes. Do you want to save them?')
            dialog.add_response("discard", "Discard")
            dialog.add_response("save", "Save")
            dialog.set_default_response("save")
            dialog.set_close_response("save")
            dialog.set_response_appearance("discard", Adw.ResponseAppearance.DESTRUCTIVE)
            dialog.set_response_appearance("save", Adw.ResponseAppearance.SUGGESTED)
            dialog.connect("response", self.on_save_journal_dialog_response)
            dialog.show()
        else:
            if date_str in self.properties:
                journal_entry = self.properties[date_str]
                self.textview.get_buffer().set_text(journal_entry)
            else:
                # key not found; date not in journal, clear editor
                self.textview.get_buffer().set_text('')


    def on_save_journal_dialog_response(self, dialog, response):
        """Respond to request to save current-1 journal entry."""
        date_str = self.date.format('%Y-%m-%d')
        buffer = self.textview.get_buffer()
        if response == "save":
            # update self.properties entry and save to file
            journal_entry = buffer.get_text(buffer.get_start_iter(), buffer.get_end_iter(), True)
            self.properties[self.old_date.format('%Y-%m-%d')] = journal_entry
            # create file for writing, 'w' means to overwrite & write whole file
            with open(self.file_path, 'w+t', encoding='UTF-8') as file:
                self.delete_empty_entries()
                jprops.store_properties(file, self.properties)
                self.mark_calendar_days()
                self.show_toast("Journal saved.")
        if date_str in self.properties:
            journal_entry = self.properties[date_str]
            buffer.set_text(journal_entry)
        else:
            buffer.set_text('')
        buffer.set_modified(False)
        self.add_title_prefix(False)


    def delete_empty_entries(self):
        """Remove any entries in self.properties that have an empty value."""
        keys_to_delete = []
        for key, value in self.properties.items():
            if value == '':
                keys_to_delete.append(key)
        for key in keys_to_delete:
            self.properties.pop(key)


    def on_new_browse_for_folder_action(self, action, parameters=None):
        """Respond to request to browse to a folder for a new journal."""
        dialog = Gtk.FileDialog()
        dialog.select_folder(self, None, self.on_folder_select)


    def on_folder_select(self, dialog, result):
        """Respond to selection of folder for a new journal."""
        try:
            folder = dialog.select_folder_finish(result)
            self.new_journal_location.set_text(folder.get_path())
        except Gtk.DialogError:
            # user cancelled or backend error
            pass


    def on_create_journal_action(self, action, parameters=None):
        """Respond to request to create a new journal."""
        location = self.new_journal_location.get_text().strip()
        journal_name = self.new_journal_name.get_text().strip()
        password_1 = self.new_journal_password_1.get_text() # do not trim whitespace
        password_2 = self.new_journal_password_2.get_text() # do not trim whitespace
        if location != '' and journal_name != '' and password_1 != '' and password_2 != '':
            if password_1 != password_2:
                self.show_toast("Passwords don't match")
            else:
                file_path = os.path.join(location, journal_name)
                self.create_journal_file(file_path, password_1)


    def create_journal_file(self, file_path, password):
        """Create a journal file."""
        if os.path.isfile(file_path):
            dialog = Adw.MessageDialog(
                transient_for=self,
                modal=True,
                heading="Replace file?",
            )
            file_name = os.path.basename(file_path)
            dialog.set_body(f'A file named {file_name} already exists. Do you want to replace it?')
            dialog.add_response("cancel", "Cancel")
            dialog.add_response("replace", "Replace")
            dialog.set_default_response("cancel")
            dialog.set_close_response("cancel")
            dialog.set_response_appearance("replace", Adw.ResponseAppearance.DESTRUCTIVE)
            dialog.connect("response", self.on_create_journal_dialog_response, file_path)
            dialog.show()
        else:
            # create file for writing, 'x' means to fail if file already exists - a failsafe
            with open(file_path, 'xt', encoding='UTF-8') as file:
                self.file_path = file_path
                self.on_create_journal_dialog_complete(file_path, file)


    def on_create_journal_dialog_response(self, dialog, response, file_path):
        """Respond to prompt to overwrite existing file."""
        if response == "replace":
            # create file for writing, 'w' means to overwrite if file already exists
            with open(file_path, 'wt', encoding='UTF-8') as file:
                self.file_path = file_path
                self.on_create_journal_dialog_complete(file_path, file)


    def on_create_journal_dialog_complete(self, file_path, file):
        """Complete journal creation process by enabling widgets,
        setting subtitle and setting focus in textview."""
        jprops.store_properties(file, self.properties)
        self.enable_widgets(True)
        self.textview.grab_focus()
        # clear textview
        self.textview.get_buffer().set_text('')
        self.textview.get_buffer().set_modified(False)
        self.window_title.set_subtitle(self.file_path)
        self.show_toast("New journal created.")


    def on_open_browse_for_journal_action(self, action, parameters=None):
        """Respond to request to browse to an existing journal."""
        dialog = Gtk.FileDialog()
        dialog.open_text_file(self, None, self.on_file_select)


    def on_file_select(self, dialog, result):
        """Respond to a file being selected in Open dialog."""
        file, encoding = dialog.open_text_file_finish(result)
        self.existing_journal_location.set_text(file.get_path())


    def on_open_journal_action(self, action, parameters=None):
        """Respond to request to open a journal."""
        self.properties = {}
        self.file_path = ''
        file_path = self.existing_journal_location.get_text()
        password = self.existing_journal_password.get_text()
        if file_path != '' and password != '':
            try:
                with open(file_path, 'a+t', encoding='UTF-8') as file:
                    file.seek(0) # reset cursor
                    self.properties = jprops.load_properties(file, collections.OrderedDict)
                    self.mark_calendar_days()
                    self.file_path = file_path
                    self.enable_widgets(True)
                    self.textview.grab_focus()
                    # load today's journal entry if exists
                    date_str = self.date.format('%Y-%m-%d')
                    journal_entry = self.properties[date_str]
                    self.textview.get_buffer().set_text(journal_entry)
                    self.textview.get_buffer().set_modified(False)
                    self.window_title.set_subtitle(file_path)
                    self.show_toast("Journal opened.")
            except UnicodeDecodeError as e:
                self.show_toast('Unable to open file.')
            except KeyError as e:
                # no entry for to display for today
                self.show_toast("Journal opened.")


    def mark_calendar_days(self):
        """Read the journal and mark the calendar days for the month that are keys."""
        self.calendar.clear_marks()
        for key, value in self.properties.items():
            if self.date.get_year() == int(key[:4]) and self.date.get_month() == int(key[5:7]) and value != '':
                self.calendar.mark_day(int(key[8:]))


    def on_save_journal_action(self, action, parameters=None):
        """Respond to request to save a journal."""
        if self.textview.get_buffer().get_modified():
            buffer = self.textview.get_buffer()
            journal_entry = buffer.get_text(buffer.get_start_iter(), buffer.get_end_iter(), True)
            date_str = self.date.format('%Y-%m-%d')
            self.properties[date_str] = journal_entry
            if self.file_path:
                with open(self.file_path, 'wt', encoding='UTF-8') as file:
                    self.delete_empty_entries()
                    #TODO encrypt
                    jprops.store_properties(file, self.properties)
                    buffer.set_modified(False)
                    self.window_title.set_title('Journal')
                    self.show_toast('Journal saved.')


    def enable_widgets(self, enable):
        """Enable/disable the inputs."""
        self.textview.set_can_target(enable)
        self.calendar.set_can_target(enable)
        self.first_button.set_can_target(enable)
        self.previous_button.set_can_target(enable)
        self.today_button.set_can_target(enable)
        self.next_button.set_can_target(enable)
        self.last_button.set_can_target(enable)
        self.save_button.set_can_target(enable)


    def show_toast(self, message):
        """Show a notification to the user."""
        toast = Adw.Toast.new(message)
        self.toast_overlay.add_toast(toast)


    def on_buffer_changed(self, buffer):
        """Handle text buffer change by prepending an asterisk to the title."""
        date_str = self.date.format('%Y-%m-%d')
        displayed_text = buffer.get_text(buffer.get_start_iter(), buffer.get_end_iter(), True)
        if date_str in self.properties:
            journal_entry = self.properties[date_str]
            if displayed_text != journal_entry:
                self.add_title_prefix(True)
            else:
                self.add_title_prefix(False)
        else:
            self.add_title_prefix(displayed_text != '')


    def add_title_prefix(self, changed):
        """Prefix the window title with a dot to indicate modified buffer."""
        title_str = self.window_title.get_title()
        if changed:
            if not title_str.startswith('• '):
                self.window_title.set_title(f'• {title_str}')
        else:
            self.window_title.set_title('Journal')
