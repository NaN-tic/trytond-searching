#This file is part searching module for Tryton.
#The COPYRIGHT file at the top level of this repository contains 
#the full copyright notices and license terms.
from trytond.pool import Pool
from .searching import *


def register():
    Pool.register(
        SearchingProfile,
        SearchingProfileLines,
        SearchingProfileGroup,
        SearchingStart,
        Model,
        module='searching', type_='model')
    Pool.register(
        Searching,
        module='searching', type_='wizard')
