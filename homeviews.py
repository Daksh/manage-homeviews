#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (C) 2013  Ignacio Rodríguez <ignacio@sugarlabs.org>
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  021101301, USA.

from gettext import gettext as _

from gi.repository import Gtk
from gi.repository import Gdk
from gi.repository import GConf
from gi.repository import SugarExt

from sugar3.activity import activity
from sugar3.graphics.toolbarbox import ToolbarBox
from sugar3.graphics.toolbarbox import ToolbarButton
from sugar3.graphics.toolbutton import ToolButton
from sugar3.activity.widgets import ActivityButton
from sugar3.activity.widgets import StopButton
from sugar3.graphics.alert import NotifyAlert

from icondialog import IconDialog

_VIEW_DIR = '/desktop/sugar/desktop'
_VIEW_ENTRY = 'view_icons'
_FAVORITE_ENTRY = 'favorite_icons'
_VIEW_KEY = '%s/%s' % (_VIEW_DIR, _VIEW_ENTRY)
_FAVORITE_KEY = '%s/%s' % (_VIEW_DIR, _FAVORITE_ENTRY)


class ManageViews(activity.Activity):
    def __init__(self, handle):
        activity.Activity.__init__(self, handle)

        self.build_toolbar()
        self._canvas = ToolbarView(self)
        width = Gdk.Screen.width()
        self._canvas.set_size_request(width, 55)

        fixed = Gtk.Fixed()
        center = (Gdk.Screen.height() / 2) - 55
        fixed.put(self._canvas, 0, center)

        eventbox = Gtk.EventBox()
        eventbox.add(fixed)
        eventbox.modify_bg(Gtk.StateType.NORMAL, Gdk.color_parse('white'))

        self.set_canvas(eventbox)
        self.show_all()

    def build_toolbar(self):
        toolbox = ToolbarBox()
        toolbar = toolbox.toolbar

        activity_button = ActivityButton(self)
        toolbar.insert(activity_button, -1)

        separator = Gtk.SeparatorToolItem()
        separator.props.draw = False
        separator.set_expand(True)
        toolbar.insert(separator, -1)

        stopbtn = StopButton(self)
        toolbar.insert(stopbtn, -1)
        toolbar.show_all()

        self.set_toolbar_box(toolbox)


class ToolbarView(ToolbarBox):
    def __init__(self, activity):
        ToolbarBox.__init__(self)

        self.add_btn = ToolButton(icon_name='list-add',
                                tooltip=_('Add new favorite view'))
        self.insert(self.add_btn, -1)
        self.add_btn.connect('clicked', self.add_view)

        self.activity = activity
        self._favorite_icons = {}
        self._view_icons = {}
        self._view_buttons = {}

        separator = Gtk.SeparatorToolItem()
        separator.props.draw = False
        separator.set_expand(True)

        self.insert(separator, -1)

        self.load_views()
        self.show_all()

    def insert(self, item, pos):
        self.toolbar.insert(item, pos)

    def remove_item(self, item):
        del(self._view_icons[item])
        del(self._favorite_icons[item])
        del(self._view_buttons[item])
        self.save_to_gconf()
        self.toolbar.remove(item)

    def load_views(self):
        client = GConf.Client.get_default()
        options = client.get(_FAVORITE_KEY)
        options2 = client.get(_VIEW_KEY)

        view_icons = []
        favorites_icons = []

        if options is not None and options2 is not None:
            for gval in options.get_list():
                favorites_icons.append(gval.get_string())

            for gval in options2.get_list():
                view_icons.append(gval.get_string())

        current = 1
        for view_icon in view_icons:
            label = _('Favorites view %d') % current
            button = ToolbarButton(label=label, icon_name=view_icon)
            page = FavoritePage(button, self, view_icon,
                favorites_icons[current - 1])
            button.set_page(page)
            self.insert(button, -1)
            self._view_icons[button] = view_icon
            self._favorite_icons[button] = favorites_icons[current - 1]
            self._view_buttons[button] = button
            current += 1

    def add_view(self, widget):
        if len(self._view_icons) >= 5:
            for x in self.activity._alerts:
                self.activity.remove_alert(x)
            alert = NotifyAlert(10)
            alert.props.title = _('Limit reached')
            alert.props.msg = _('You have reached the maximum limit of '
                'favorites views, please delete some before continuing.')
            self.activity.add_alert(alert)
            alert.connect('response',
                lambda x, y: self.activity.remove_alert(x))
            return

        label = _('New favorite view')
        button = ToolbarButton(label=label, icon_name='view-radial')
        page = FavoritePage(button, self, 'view-radial', 'emblem-favorite')
        button.set_page(page)

        self._view_icons[button] = 'view-radial'
        self._favorite_icons[button] = 'emblem-favorite'
        self._view_buttons[button] = button

        self.insert(button, -1)
        self.save_to_gconf()
        self.show_all()

    def save_to_gconf(self, icon=False):

        view_icons = []
        favorite_icons = []

        for button in self._view_buttons:
            view_icons.append(self._view_icons[button])
            favorite_icons.append(self._favorite_icons[button])

        client = GConf.Client.get_default()
        SugarExt.gconf_client_set_string_list(client,
                                              _FAVORITE_KEY,
                                              favorite_icons)

        SugarExt.gconf_client_set_string_list(client,
                                              _VIEW_KEY,
                                              view_icons)

        if icon:
            for x in self.activity._alerts:
                self.activity.remove_alert(x)
            alert = NotifyAlert(5)
            alert.props.title = _('Icon')
            alert.props.msg = _('For see icons, restart sugar is needed.')
            self.activity.add_alert(alert)
            alert.connect('response',
                lambda x, y: self.activity.remove_alert(x))


class FavoritePage(Gtk.Toolbar):
    def __init__(self, button, toolbar, view_icon, favorite_icon):
        Gtk.Toolbar.__init__(self)

        self.toolbar = toolbar
        self.button = button
        self.view_icon = view_icon
        self.favorite_icon = favorite_icon

        self.set_view_icon = ToolButton(view_icon)
        self.set_view_icon.set_tooltip(_('Set toolbar icon'))
        self.set_view_icon.connect('clicked', self.set_icon, False)

        self.set_favorite_icon = ToolButton(favorite_icon)
        self.set_favorite_icon.set_tooltip(_('Set the icon of favorites list'))
        self.set_favorite_icon.connect('clicked', self.set_icon, True)

        self.remove_btn = ToolButton('list-remove')
        self.remove_btn.set_tooltip(_('Remove favorite view'))
        self.remove_btn.connect('clicked', self.remove_view)

        separator = Gtk.SeparatorToolItem()
        separator.props.draw = False
        separator.set_expand(True)

        self.insert(self.set_view_icon, -1)
        self.insert(self.set_favorite_icon, -1)
        self.insert(separator, -1)
        self.insert(self.remove_btn, -1)
        self.show_all()

    def set_icon(self, widget, favorite=False, window=None):
        if not window:
            dialog = IconDialog()
            dialog.show_all()
            dialog.connect('destroy', self.set_icon, favorite, dialog)

        if window:
            response = window.get_icon()
            if not response:
                return
            if favorite:
                self.set_favorite_icon.set_icon_name(response)
                self.toolbar._favorite_icons[self.button] = response
            else:
                self.set_view_icon.set_icon_name(response)
                self.toolbar._view_icons[self.button] = response
                self.button.set_icon_name(response)

            self.toolbar.save_to_gconf(True)

    def remove_view(self, widget):
        self.button.set_expanded(False)
        self.toolbar.remove_item(self.button)
