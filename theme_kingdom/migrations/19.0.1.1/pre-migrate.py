# -*- coding: utf-8 -*-
"""Rename kingdom.manufacturer → kingdom.brand before ORM loads the new model."""


def migrate(cr, version):
    from odoo.addons.theme_kingdom import hooks
    hooks._rename_manufacturer_to_brand(cr)
