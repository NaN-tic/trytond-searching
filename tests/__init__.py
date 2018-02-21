# This file is part searching module for Tryton.
# The COPYRIGHT file at the top level of this repository contains
# the full copyright notices and license terms.
try:
    from trytond.modules.searching.tests.test_searching import suite
except ImportError:
    from .test_searching import suite

__all__ = ['suite']
