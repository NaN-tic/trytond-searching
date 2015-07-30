# This file is part searching module for Tryton.
# The COPYRIGHT file at the top level of this repository contains
# the full copyright notices and license terms.
from datetime import datetime
from decimal import Decimal
from trytond.model import ModelView, ModelSQL, fields
from trytond.model.fields import depends
from trytond.wizard import Wizard, StateView, StateAction, Button
from trytond.pool import Pool, PoolMeta
from trytond.transaction import Transaction
from trytond.pyson import Eval, PYSONEncoder, Id, Or

__all__ = ['SearchingProfile', 'SearchingProfileLine',
    'SearchingProfileGroup', 'SearchingStart', 'Searching', 'Model']
__metaclass__ = PoolMeta

_OPERATORS = [
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
]


class SearchingProfile(ModelSQL, ModelView):
    'Searching Profile'
    __name__ = 'searching.profile'
    name = fields.Char('Name', required=True)
    model = fields.Many2One('ir.model', 'Model', required=True,
        domain=[('searching_enabled', '=', True)],
        states={
            'readonly': Eval('lines', False),
            },
        depends=['lines'])
    model_name = fields.Function(fields.Char('Model Name'),
        'on_change_with_model_name')
    python_domain = fields.Boolean('Python Domain')
    domain = fields.Text('Domain',
        states={
            'required': Eval('python_domain', False),
            'invisible': Or(~Eval('model'), ~Eval('python_domain', False)),
            },
        depends=['model', 'python_domain'],
        help="Return a domain with a list of tuples:\n" \
            "domain = [(<field name>, <operator>, <operand>)]")
    lines = fields.One2Many('searching.profile.line', 'profile', 'Lines',
        states={
            'invisible': Or(~Eval('model'), Eval('python_domain', False)),
            },
        depends=['model', 'python_domain'])
    condition = fields.Function(fields.Char('Condition'),
        'get_condition')
    profile_groups = fields.Many2Many('searching.profile-res.group', 'profile',
        'group', 'Groups',
        states={
            'invisible': ~Eval('groups', []).contains(Id('res', 'group_admin')
                ),
            },
        help='User groups that will be able to use this search profile.')
    action = fields.Many2One('ir.action.act_window', 'Action',
        domain=[('res_model', '=', Eval('model_name'))],
        depends=['model_name'],
        help='Action Window to display the results')

    @classmethod
    def __setup__(cls):
        super(SearchingProfile, cls).__setup__()
        cls._error_messages.update({
                'domain_field_error': 'Error in field domain: %s',
                'domain_field_help': 'This field must returns a variable '
                    'called "domain" with a Tryton domain.'
                })

    @staticmethod
    def default_python_domain():
        return False

    def get_rec_name(self, name):
        return '%s - %s' % (self.name, self.get_condition(name))

    @depends('model')
    def on_change_with_model_name(self, name=None):
        return self.model.model if self.model else None

    def get_condition(self, name):
        condition = []
        for line in self.lines:
            if line.subfield:
                condition.append("('%s.%s','%s','%s')" % (line.field.name,
                    line.subfield.name, line.operator, line.value))
            else:
                condition.append("('%s', '%s', '%s')" % (line.field.name,
                    line.operator, line.value))

        return ', '.join(condition)

    def get_domain(self):
        if not self.python_domain:
            domain = self.build_domain()
        else:
            domain = self.exec_domain()
        if self.action and self.action.domain:
            domain += eval(self.action.domain)
        return domain

    def build_domain(self, lines=None):
        if lines is None:
            lines = self.lines
        condition_and = []
        condition_or = []
        for line in lines:
            field = line.field.name
            if line.subfield:
                field = '%s.%s' % (line.field.name, line.subfield.name)
            if line.condition == 'AND':
                condition_and.append(
                    (field, line.operator, line.get_value()),
                    )
            else:
                condition_or.append(
                    (field, line.operator, line.get_value()),
                    )

        domain = []
        if condition_or:
            condition_or.insert(0, 'OR')
            domain.append(condition_or)
        if condition_and:
            domain.append(condition_and)
        return domain

    def exec_domain(self, domain=None):
        if domain is None:
            domain = self.domain
        try:
            exec domain
        except TypeError, e:
            self.raise_user_error('domain_field_error',
                error_args=(e.message,))
        if not domain:
            self.raise_user_error('domain_field_error',
                error_args=(self.raise_user_error('domain_field_help',
                    raise_exception=False),))
        return domain


class SearchingProfileLine(ModelSQL, ModelView):
    'Searching Profile Line'
    __name__ = 'searching.profile.line'
    profile = fields.Many2One('searching.profile', 'Profile',
        ondelete='CASCADE', select=True)
    sequence = fields.Integer('Sequence')
    condition = fields.Selection([
            ('AND', 'AND'),
            ('OR', 'OR'),
            ], 'Condition', required=True)
    field = fields.Many2One('ir.model.field', 'Field',
        domain=[('model', '=',
            Eval('_parent_profile', Eval('context', {})).get('model', -1))],
        select=True, required=True)
    field_type = fields.Function(fields.Char('Field Type'),
        'on_change_with_field_type')
    submodel = fields.Function(fields.Many2One('ir.model', 'Submodel'),
        'on_change_with_submodel')
    subfield = fields.Many2One('ir.model.field', 'Subfield',
        domain=[('model', '=', Eval('submodel'))],
        states={
            'invisible': ~Eval('field_type').in_(
                ['many2one', 'one2many', 'many2many']),
            'required': Eval('field_type').in_(
                ['many2one', 'one2many', 'many2many']),
        }, depends=['field_type', 'submodel'], select=True)
    operator = fields.Selection(_OPERATORS, 'Operator', required=True)
    value = fields.Char('Value')

    @classmethod
    def __setup__(cls):
        super(SearchingProfileLine, cls).__setup__()
        cls._order.insert(0, ('sequence', 'ASC'))
        cls._error_messages.update({
                'not_implemented_error':
                    'Error. Field of type %s is not implemented yet.',
                'datetime_format_error':
                    'Error building domain of type DateTime or Timestamp. '
                    'Please, check the format:\n\n'
                    'Field: \'%s\'\n'
                    'Value: \'%s\'\n'
                    'Format: \'%%d/%%m/%%Y %%H:%%M:%%S\'',
                'date_format_error':
                    'Error building domain of type Date. '
                    'Please, check the format:\n\n'
                    'Field: \'%s\'\n'
                    'Value: \'%s\'\n'
                    'Format: \'%%d/%%m/%%Y\'',
                'number_format_error':
                    'Error building domain of type Float. '
                    'Please, ensure you have put a number.\n\n'
                    'Field: \'%s\'\n'
                    'Value: \'%s\'\n',
                })

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

    def get_value_boolean(self):
        return bool(self.value)

    def get_value_integer(self):
        try:
            return int(self.value)
        except ValueError:
            self.raise_user_error('number_format_error',
                error_args=(self.field.name, self.value))

    def get_value_float(self):
        try:
            return float(self.value)
        except ValueError:
            self.raise_user_error('number_format_error',
                error_args=(self.field.name, self.value))

    def get_value_numeric(self):
        try:
            return Decimal(self.value)
        except ValueError:
            self.raise_user_error('number_format_error',
                error_args=(self.field.name, self.value))

    def get_value_date(self):
        try:
            return datetime.strptime(self.value, '%d/%m/%Y').date()
        except ValueError:
            self.raise_user_error('date_format_error',
                error_args=(self.field.name, self.value))

    def get_value_datetime(self):
        try:
            return datetime.strptime(self.value, '%d/%m/%Y %H:%M:%S')
        except ValueError:
            self.raise_user_error('datetime_format_error',
                error_args=(self.field.name, self.value))

    def get_value_timestamp(self):
        return self.get_value_datetime()

    def get_value(self):
        if self.field_type in ('boolean', 'integer', 'float', 'numeric',
                'date', 'datetime', 'timestamp'):
            return getattr(self, 'get_value_%s' % self.field_type)()
        elif self.field_type in ('char', 'text', 'selection', 'reference',
                'many2one', 'one2many'):
            return self.value
        self.raise_user_error('not_implemented_error',
            error_args=(self.field_type,))

    def get_rec_name(self, name):
        if self.subfield:
            return "'%s.%s','%s','%s'" % (self.field.name, self.subfield.name,
                self.operator, self.value)
        else:
            return "'%s','%s','%s'" % (self.field.name,
                self.operator, self.value)

    @fields.depends('field')
    def on_change_field(self):
        return {'subfield': None}

    @fields.depends('field')
    def on_change_with_field_type(self, name=None):
        if self.field:
            return self.field.ttype
        return ''

    @fields.depends('field', '_parent_profile.model')
    def on_change_with_submodel(self, name=None):
        Model = Pool().get('ir.model')
        if getattr(self, 'profile'):
            profile_model = self.profile.model
        elif 'model' in Transaction().context:
            profile_model = Model(Transaction().context.get('model'))
        else:
            return None
        ProfileModel = Pool().get(profile_model.model)
        if (self.field and
                self.field.ttype in ['many2one', 'one2many', 'many2many']):
            field = ProfileModel._fields[self.field.name]
            relation = field.get_target().__name__
            models = Model.search([('model', '=', relation)])
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
                ('profile_groups', 'in',
                    Eval('context', {}).get('groups', [])),
                ('profile_groups', '=', None),
            ],
            ],
        states={
            'readonly': Eval('lines', False),
            },
        depends=['lines'])
    model = fields.Function(fields.Many2One('ir.model', 'Model'),
        'on_change_with_model')
    python_domain = fields.Function(fields.Boolean('Python Domain'),
        'on_change_with_python_domain')
    domain = fields.Text('Domain',
        states={
            'required': Eval('python_domain', False),
            'invisible': Or(~Eval('profile'), ~Eval('python_domain', False)),
            },
        depends=['profile', 'python_domain'],
        help="Return a domain with a list of tuples:\n" \
            "domain = [(<field name>, <operator>, <operand>)]")
    lines = fields.One2Many('searching.profile.line', None, 'Lines',
        states={
            'invisible': Or(~Eval('profile'), Eval('python_domain', False)),
            },
        context={
            'model': Eval('model'),
            },
        depends=['profile', 'python_domain', 'model'],)

    @fields.depends('profile')
    def on_change_with_model(self, name=None):
        if self.profile:
            return self.profile.model.id
        return None

    @fields.depends('profile')
    def on_change_with_python_domain(self, name=None):
        if self.profile:
            return self.profile.python_domain
        return False

    @fields.depends('profile')
    def on_change_with_domain(self, name=None):
        if self.profile:
            return self.profile.domain
        return None

    @fields.depends('profile')
    def on_change_with_lines(self, name=None):
        lines = []
        if self.profile:
            lines = [x.id for x in self.profile.lines]
        return lines


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
        Action = Pool().get('ir.action')

        profile = self.start.profile
        model = profile.model
        model_model = profile.model.model
        Model = Pool().get(model_model)

        if not self.start.python_domain:
            domain = profile.build_domain(self.start.lines)
        else:
            domain = profile.exec_domain(self.start.domain)

        if profile.action and profile.action.domain:
            domain = domain + eval(profile.action.domain)

        try:
            Model.search(domain)
        except:
            with Transaction().new_cursor():
                self.raise_user_error('error_domain', str(domain))

        # return custom action window
        if profile.action:
            action = profile.action
            action = Action.get_action_values(action.type, [action.id])[0]
            action['res_model'] = model_model
            action['name'] = '%s - %s' % (model.name, profile.name)
            action['pyson_domain'] = PYSONEncoder().encode(domain)
            action['pyson_context'] = profile.action.context or {}
            return action, {}

        # return default action window
        return {
            'id': -1,
            'name': '%s - %s' % (model.name, profile.name),
            'model': model_model,
            'res_model': model_model,
            'type': 'ir.action.act_window',
            'pyson_domain': PYSONEncoder().encode(domain),
            'pyson_context': {},
            'pyson_order': '[]',
            'pyson_search_value': '[]',
            'domains': [],
            }, {}


class Model(ModelSQL, ModelView):
    __name__ = 'ir.model'
    searching_enabled = fields.Boolean('Searching Enabled',
        help='Check if you want this model to be available in '
        'Searching Profiles.')
