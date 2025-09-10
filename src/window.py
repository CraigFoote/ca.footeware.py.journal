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
import os
import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Adw
from gi.repository import Gtk
from gi.repository import Gio
from gi.repository import GLib
from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64
import jprops
from sortedcontainers import SortedDict


@Gtk.Template(resource_path='/ca/footeware/py/journal/window.ui')
class JournalWindow(Adw.ApplicationWindow):
    """The main window class."""
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
    toast_overlay_new = Gtk.Template.Child()
    toast_overlay_open = Gtk.Template.Child()
    toast_overlay_editor = Gtk.Template.Child()
    window_title = Gtk.Template.Child()
    stack = Gtk.Template.Child()
    new_open_button_box = Gtk.Template.Child()
    new_button = Gtk.Template.Child()
    new_page_box = Gtk.Template.Child()
    open_page_box = Gtk.Template.Child()
    editor_page_box = Gtk.Template.Child()
    back_button = Gtk.Template.Child()


    def __init__(self, **kwargs):
        """Initialize this Journal instance."""
        super().__init__(**kwargs)

        # read UI file
        self.init_template()

        # open stack to its initial page
        self.stack.set_visible_child(self.new_open_button_box)

        # 'Back' action
        back_action = Gio.SimpleAction.new("back_button", None)
        back_action.connect("activate", self.on_back_action)
        self.add_action(back_action)

        # 'New' journal action
        new_journal_action = Gio.SimpleAction.new("new_journal", None)
        new_journal_action.connect("activate", self.on_new_journal_action)
        self.add_action(new_journal_action)

        # 'Open' existing journal action
        open_existing_journal_action = Gio.SimpleAction.new("open_existing_journal", None)
        open_existing_journal_action.connect("activate", self.on_open_existing_journal_action)
        self.add_action(open_existing_journal_action)

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

        self.journal = None
        self.date = self.calendar.get_date()


    def on_back_action(self, action, parameters=None):
        """Respond to the Back button being clicked."""
        self.back_button.set_sensitive(False)
        self.back_button.set_visible(False)
        self.stack.set_visible_child(self.new_open_button_box)


    def on_new_journal_action(self, action, parameters=None):
        """Respond to the New [journal] button being clicked."""
        self.stack.set_visible_child(self.new_page_box)
        self.back_button.set_sensitive(True)
        self.back_button.set_visible(True)


    def on_open_existing_journal_action(self, action, parameters=None):
        """Respond to the Open [existing journal] button being clicked."""
        self.stack.set_visible_child(self.open_page_box)
        self.back_button.set_sensitive(True)
        self.back_button.set_visible(True)


    def on_first_action(self, action, parameters=None):
        """Respond to the First button being clicked."""
        if self.journal is not None:
            keys = self.journal.get_keys()
            if len(keys) > 0:
                first = sorted(list(keys))[0]
                date = self.date_from_str(first)
                self.calendar.select_day(date)
                self.mark_calendar_days()


    def on_previous_action(self, action, parameters=None):
        """Respond to the Previous button being clicked."""
        if self.journal is not None:
            current_date = self.calendar.get_date()
            current_date_str = current_date.format('%Y-%m-%d')
            keys = sorted(list(self.journal.get_keys()))
            # find index of currently selected date, if exists, then find previous item
            previous_key = None
            try:
                current_index = list(keys).index(current_date_str)
                if current_index - 1 >= 0:
                    previous_key_index = current_index - 1
                    previous_key = list(keys)[previous_key_index]
            except ValueError:
                # current date has no entry
                pass
            # no entry for selected date
            if previous_key is None:
                # if selected date is before last entry, display last entry
                if len(keys) > 0:
                    last_key = list(self.journal.get_keys())[0]
                    if current_date_str < last_key: # we don't care if it's >
                        previous_key = last_key
                    else:
                        # if selected date has no entry and is between two entries, select earlier one
                        # find next lower entry
                        copy = list(keys).copy()
                        copy.reverse() # easier to go thru keys reversed
                        for key in list(copy):
                            if current_date_str > key:
                                # previous key is lower entry
                                previous_key = copy[copy.index(key)]
                                break
            if previous_key is not None:
                date = self.date_from_str(previous_key)
                self.calendar.select_day(date)
                self.mark_calendar_days()


    def on_today_action(self, action, parameters=None):
        if self.journal is not None:
            """Respond to request to navigate to 'today' in calendar."""
            self.calendar.select_day(GLib.DateTime.new_now_local())
            self.date = self.calendar.get_date();
            self.mark_calendar_days()


    def on_next_action(self, action, parameters=None):
        """Respond to the Next button being clicked."""
        if self.journal is not None and len(self.journal.get_entries()) > 0:
            current_date = self.calendar.get_date()
            current_date_str = current_date.format('%Y-%m-%d')
            keys = sorted(list(self.journal.get_keys()))
            # find index of currently selected date, if exists, then find next item
            next_key = None
            try:
                current_index = list(keys).index(current_date_str)
                if current_index + 1 < len(keys):
                    next_key_index = current_index + 1
                    next_key = list(keys)[next_key_index]
            except ValueError:
                # current date has no entry
                pass
            # no entry for selected date
            if next_key is None:
                # if selected date is before first entry, display first entry
                first_key = list(self.journal.get_keys())[0]
                if current_date_str < first_key: # we don't care if it's >
                    next_key = first_key
                else:
                    # if selected date has no entry and is between two entries, select later one
                    upper_entry = None
                    copy = list(keys).copy()
                    copy.reverse()
                    for key in list(copy): # entries are in SortedDict (low to high)
                        if key < current_date_str:
                            # previous key is next higher entry
                            upper_entry = copy[copy.index(key) - 1]
                            break
                    if upper_entry is not None:
                        next_key = upper_entry
            if next_key is not None:
                date = self.date_from_str(next_key)
                self.calendar.select_day(date)
                self.mark_calendar_days()


    def on_last_action(self, action, parameters=None):
        """Respond to the Last button being clicked."""
        if self.journal is not None:
            keys = self.journal.get_keys()
            if len(keys) > 0:
                last = sorted(list(keys))[len(keys) - 1]
                date = self.date_from_str(last)
                self.calendar.select_day(date)
                self.mark_calendar_days()


    def date_from_str(self, date_str):
        """Parses a string of format %Y-%m-%d into a GLib.DateTime."""
        year = date_str[:4]
        month = date_str[5:7]
        day = date_str[8:]
        return GLib.DateTime.new_local(int(year), int(month), int(day), 0, 0, 0)


    def on_prev_month(self, calendar):
        """Respond to pressing of Previous Month button."""
        if self.journal is not None:
            self.date = calendar.get_date()
            self.mark_calendar_days();


    def on_next_month(self, calendar):
        """Respond to pressing of Next Month button."""
        if self.journal is not None:
            self.date = calendar.get_date()
            self.mark_calendar_days();


    def on_prev_year(self, calendar):
        """Respond to pressing of Previous Year button."""
        if self.journal is not None:
            self.date = calendar.get_date()
            self.mark_calendar_days();


    def on_next_year(self, calendar):
        """Respond to pressing of Next Year button."""
        if self.journal is not None:
            self.date = calendar.get_date()
            self.mark_calendar_days();


    def on_day_selected(self, calendar):
        """React to a new day being selected in the calendar."""
        if self.journal is not None:
            # store date from previous selection, we may need to save its entry
            self.old_date = self.date
            self.date = calendar.get_date()
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
                if self.journal.contains_key(self.date):
                    journal_entry = self.journal.get_entry(self.date)
                    self.textview.get_buffer().set_text(journal_entry)
                else:
                    # key not found; date not in journal, clear editor
                    self.textview.get_buffer().set_text('')


    def on_save_journal_dialog_response(self, dialog, response):
        """Respond to request to save current-1 journal entry."""
        if self.journal is not None:
            buffer = self.textview.get_buffer()
            if response == "save":
                # update self.journal entry and save to file
                journal_entry = buffer.get_text(buffer.get_start_iter(), buffer.get_end_iter(), True)
                self.journal.add_entry(self.old_date, journal_entry) # saves
                self.mark_calendar_days()
                self.toast_overlay_editor.add_toast(Adw.Toast.new("Journal saved"))
            date_str = self.calendar.get_date()
            if date_str in self.journal.get_keys():
                journal_entry = self.journal.get_entry(date_str)
                buffer.set_text(journal_entry)
            else:
                buffer.set_text('')
            buffer.set_modified(False)
            self.add_title_prefix(False)


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
                self.toast_overlay_new.add_toast(Adw.Toast.new("Passwords don't match"))
            else:
                file_path = os.path.join(location, journal_name)
                self.password = password_1
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
        self.journal = Journal(file_path, self.password)
        self.date = self.calendar.get_date()
        self.textview.grab_focus()
        # clear textview
        self.textview.get_buffer().set_text('')
        self.textview.get_buffer().set_modified(False)
        self.window_title.set_subtitle(self.file_path)
        self.back_button.set_sensitive(False)
        self.back_button.set_visible(False)
        self.stack.set_visible_child(self.editor_page_box)


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
        self.password = self.existing_journal_password.get_text()
        if file_path != '' and self.password != '':
            try:
                self.journal = Journal(file_path, self.password)
                self.mark_calendar_days()
                self.date = self.calendar.get_date()
                self.textview.grab_focus()
                # load today's journal entry if exists
                try:
                    journal_entry = self.journal.get_entry(self.calendar.get_date())
                    self.textview.get_buffer().set_text(journal_entry)
                except KeyError:
                    # no entry for today
                    pass
                self.textview.get_buffer().set_modified(False)
                self.window_title.set_subtitle(file_path)
                self.back_button.set_sensitive(False)
                self.back_button.set_visible(False)
                self.stack.set_visible_child(self.editor_page_box)
            except InvalidToken as e:
                self.toast_overlay_open.add_toast(Adw.Toast.new("'InvalidToken' error. Is the password correct?"))


    def mark_calendar_days(self):
        """Read the journal and mark the calendar days for the month that are keys."""
        if self.journal is not None:
            self.calendar.clear_marks()
            for key, value in self.journal.get_entries():
                date = self.calendar.get_date()
                if date.get_year() == int(key[:4]) and date.get_month() == int(key[5:7]) and value != '':
                    self.calendar.mark_day(int(key[8:]))


    def on_save_journal_action(self, action, parameters=None):
        """Respond to request to save a journal."""
        if self.journal is not None:
            if self.textview.get_buffer().get_modified():
                buffer = self.textview.get_buffer()
                journal_entry = buffer.get_text(buffer.get_start_iter(), buffer.get_end_iter(), True)
                self.journal.add_entry(self.calendar.get_date(), journal_entry)
                self.mark_calendar_days()
                buffer.set_modified(False)
                self.window_title.set_title('Journal')
                self.toast_overlay_editor.add_toast(Adw.Toast.new("Journal saved"))


    def on_buffer_changed(self, buffer):
        """Handle text buffer change by prepending an asterisk to the title."""
        displayed_text = buffer.get_text(buffer.get_start_iter(), buffer.get_end_iter(), True)
        self.date = self.calendar.get_date()
        date_str = self.date.format('%Y-%m-%d')
        if date_str in self.journal.get_keys():
            journal_entry = self.journal.get_entry(self.date)
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


class Journal:
    """A map where the keys are dates in the format %Y-%m-%d and the values are textual entries."""

    def __init__(self, file_path, password):
        """Initialization."""
        self.file_path = file_path
        self.password = password
        self.entries = {}
        # load entries if any
        try:
            with open(file_path, 'rt', encoding='UTF-8') as file:
                encrypted = jprops.load_properties(file, SortedDict)
                for key, value in encrypted.items():
                    decrypted_value = self.decrypt(value, self.password)
                    self.entries[key] = decrypted_value
        except FileNotFoundError:
            pass  # No existing journal file
        self.save()


    def save(self):
        """Save all entries to file."""
        with open(self.file_path, 'wt', encoding='UTF-8') as file:
            self.prune_empty_values()
            encrypted = {}
            for key, value in sorted(list(self.entries.items())):
                encrypted_value = self.encrypt(value, self.password)
                encrypted[key] = encrypted_value
            jprops.store_properties(file, encrypted)


    def prune_empty_values(self):
        """Remove from self.entries those that have a blank value."""
        keys_to_pop = []
        for key, value in self.entries.items():
            if value == '':
                keys_to_pop.append(key)
        for key in keys_to_pop:
            self.entries.pop(key)


    def add_entry(self, date, text):
        """Add a new entry."""
        date_str = date.format('%Y-%m-%d')
        self.entries[date_str] = text
        self.save()


    def get_keys(self):
        """Get all the dates in this journal."""
        return self.entries.keys()


    def get_entry(self, key):
        """Get a date's entry.'"""
        if isinstance(key, GLib.DateTime):
            key = key.format('%Y-%m-%d')
        return self.entries[key]


    def get_entries(self):
        """Get all entries in this journal."""
        return self.entries.items()


    def remove_entry(self, key):
        """Remove an entry."""
        if isinstance(key, GLib.DateTime):
            key = key.format('%Y-%m-%d')
        self.entries.pop(key)


    def contains_key(self, key):
        """Determines if the provided key is a key in self.entries."""
        index = None
        if isinstance(key, GLib.DateTime):
            key = key.format('%Y-%m-%d')
        try:
            index = list(self.entries.keys()).index(key)
            return index is not None
        except ValueError:
            # no entry for key
            return False


    def encrypt(self, plaintext, password):
        """Encrypt the provided `plaintext` using provided `password`."""
        if isinstance(plaintext, str):
            plaintext = plaintext.encode("utf-8")
        encrypted_bytes = self.cipherFernet(password.encode("utf-8")).encrypt(plaintext)
        return encrypted_bytes.decode("utf-8")


    def decrypt(self, ciphertext, password):
        """Decrypt the provided `ciphertext` using provided `password`."""
        decrypted_bytes = self.cipherFernet(password.encode("utf-8")).decrypt(ciphertext)
        return decrypted_bytes.decode("utf-8")


    def cipherFernet(self, password):
        """Create a hairy little Fernet."""
        key = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=b'abcd', iterations=1000, backend=default_backend()).derive(password)
        return Fernet(base64.urlsafe_b64encode(key))
