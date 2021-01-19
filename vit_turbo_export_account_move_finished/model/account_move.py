from odoo import api, fields, models, _

class account_move(models.Model):
    _name = 'account.move'
    _inherit = 'account.move'

    is_exported = fields.Boolean(string="Is Exported", default=False )
    date_exported = fields.Datetime(string="Exported Date", required=False, )

