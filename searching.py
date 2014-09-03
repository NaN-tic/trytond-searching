#This file is part searching module for Tryton.
#The COPYRIGHT file at the top level of this repository contains 
#the full copyright notices and license terms.
from trytond.model import ModelView, ModelSQL, fields
from trytond.wizard import Wizard, StateView, StateAction, Button
from trytond.pool import Pool, PoolMeta
from trytond.pyson import Eval, Id
import json

__all__ = ['SearchingProfile', 'SearchingProfileLines', 'SearchingProfileGroup',
    'SearchingStart', 'Searching', 'Model']
__metaclass__ = PoolMeta


class SearchingProfile(ModelSQL, ModelView):
    'Searching Profile'
    __name__ = 'searching.profile'
    name = fields.Char('Name', required=True)
    model = fields.Many2One('ir.model', 'Model', required=True,
        domain=[('searching_enabled', '=', True)])
    lines = fields.One2Many('searching.profile.line', 'profile', 'Lines',
        states={
            'invisible': Eval('python_domain', True),
            },
        depends=['python_domain'])
    condition = fields.Function(fields.Char('Condition'),
        'get_condition')
    profile_groups = fields.Many2Many('searching.profile-res.group', 'profile',
        'group', 'Groups',
        states={
            'invisible': ~Eval('groups', []).contains(Id('res', 'group_admin')),
            },
        help='User groups that will be able to see use this profile.')
    python_domain = fields.Boolean('Python Domain')
    domain = fields.Text('Domain', 
        states={
            'required': Eval('python_domain', True),
            'invisible': ~Eval('python_domain', False),
            },
        depends=['python_domain'])

    @staticmethod
    def default_python_domain():
        return False

    def get_rec_name(self, name):
        condition = []
        for line in self.lines:
            condition.append("('%s', '%s', '%s')" % (
                line.field.name, line.operator, line.value
                ))
        return '%s - %s' % (self.name, ', '.join(condition))

    def get_condition(self, name):
        condition = []
        for line in self.lines:
            condition.append("('%s', '%s', '%s')" % (
                line.field.name, line.operator, line.value
                ))
        return ', '.join(condition)


class SearchingProfileLines(ModelSQL, ModelView):
    'Searching Profile Line'
    __name__ = 'searching.profile.line'
    profile = fields.Many2One('searching.profile', 'Profile', ondelete='CASCADE',
        select=True)
    field = fields.Many2One('ir.model.field', 'Field',
        domain=[('model', '=', Eval('_parent_profile', {}).get('model'))],
        select=True, required=True)
    field_type = fields.Function(fields.Char('Field Type'),
        'on_change_with_field_type')
    submodel = fields.Function(fields.Many2One('ir.model', 'Submodel'),
        'on_change_with_submodel')
    subfield = fields.Many2One('ir.model.field', 'Subfield',
        domain=[('model', '=',  Eval('submodel'))],
        states={
            'invisible': Eval('field_type') != 'one2many',
            'required': Eval('field_type') == 'one2many',
        }, depends=['field_type', 'submodel'], select=True)
    operator = fields.Selection([
            ('=', '='),
            ('!=', '!='),
            ('like', 'like'),
            ('not like', 'not like'),
            ('ilike', 'ilike'),
            ('not ilike', 'not ilike'),
            ('in', 'in'),
            ('not in', 'not in'),
            ('<', '<'),
            ('>', '>'),
            ('<=', '<='),
            ('>=', '>='),
        ], 'Operator', required=True)
    condition = fields.Selection([
            ('AND', 'AND'),
            ('OR', 'OR'),
        ], 'Condition', required=True)
    value = fields.Char('Value', required=True)
    sequence = fields.Integer('Sequence')

    @classmethod
    def __setup__(cls):
        super(SearchingProfileLines, cls).__setup__()
        cls._order.insert(0, ('sequence', 'ASC'))

    @staticmethod
    def order_sequence(tables):
        table, _ = tables[None]
        return [table.sequence == None, table.sequence]

    @staticmethod
    def default_sequence():
        return 0

    @staticmethod
    def default_condition():
        return 'AND'

    def get_rec_name(self, name):
        return "'%s','%s','%s'" % (self.field, self.operator, self.value)

    @fields.depends('field')
    def on_change_with_field_type(self, name=None):
        if self.field:
            return self.field.ttype
        return ''

    @fields.depends('field')
    def on_change_with_submodel(self, name=None):
        Model = Pool().get('ir.model')
        if self.field and self.field.ttype == 'one2many':
            models = Model.search([('model', '=', self.field.relation)])
            return models[0].id if models else None
        return None


class SearchingProfileGroup(ModelSQL):
    "Searching Profile - Group"
    __name__ = 'searching.profile-res.group'
    profile = fields.Many2One('searching.profile', 'Profile', required=True)
    group = fields.Many2One('res.group', 'Group', required=True)


class EmptyStateAction(StateAction):
    def __init__(self):
        super(EmptyStateAction, self).__init__(None)

    def get_action(self):
        return {}


class SearchingStart(ModelView):
    'Searching Start'
    __name__ = 'searching.start'
    profile = fields.Many2One('searching.profile', 'Profile', required=True,
        domain=[
            ['OR',
                ('profile_groups', 'in', Eval('context', {}).get('groups', [])),
                ('profile_groups', '=', None),
            ],
        ],)


class Searching(Wizard):
    'Searching'
    __name__ = 'searching'
    start = StateView('searching.start',
        'searching.searching_start_view_form', [
            Button('Cancel', 'end', 'tryton-cancel'),
            Button('Search', 'open_', 'tryton-ok', default=True),
            ])
    open_ = EmptyStateAction()

    @classmethod
    def __setup__(cls):
        super(Searching, cls).__setup__()
        cls._error_messages.update({
                'error_domain': ('Error domain "%s"'),
                })

    def do_open_(self, action):
        profile = self.start.profile
        model = profile.model
        model_name = profile.model.model
        Model = Pool().get(model_name)

        if not profile.python_domain:
            condition_and = []
            condition_or = []
            for line in profile.lines:
                field = line.field.name
                if line.subfield:
                    field = '%s.%s' % (line.field.name, line.subfield.name)
                if line.condition == 'AND':
                    condition_and.append((field, line.operator, line.value))
                else:
                    condition_or.append((field, line.operator, line.value))

            condition = []
            if condition_or:
                condition.append('OR')
                condition.append([condition_or])
            if condition_and:
                condition.append(condition_and)
        else:
            condition = eval(profile.domain)

        try:
            records = Model.search(condition)
        except:
            self.raise_user_error('error_domain', condition)

        domain = [('id', 'in', [x.id for x in records])]
        domain = json.dumps(domain)
        context = {}
        return {
            'name': '%s - %s' % (profile.name, model.name),
            'model': model_name,
            'res_model': model_name,
            'type': 'ir.action.act_window',
            'pyson_domain': domain,
            'pyson_context': context,
            'pyson_order': '[]',
            'pyson_search_value': '[]',
            'domains': [],
            }, {}


class Model(ModelSQL, ModelView):
    __name__ = 'ir.model'
    searching_enabled = fields.Boolean('Searching Enabled', help='Check if you want '
        'this model to be available in Searching Profiles.')
