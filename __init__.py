# This file is part searching module for Tryton.
# The COPYRIGHT file at the top level of this repository contains
# the full copyright notices and license terms.
from trytond.pool import Pool
from . import searching


def register():
    Pool.register(
        searching.SearchingProfile,
        searching.SearchingProfileLine,
        searching.SearchingProfileGroup,
        searching.SearchingStart,
        searching.Model,
        module='searching', type_='model')
    Pool.register(
        searching.Searching,
        module='searching', type_='wizard')
