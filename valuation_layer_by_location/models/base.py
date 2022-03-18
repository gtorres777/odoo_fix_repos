from lxml import etree
from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError
from odoo.tools import float_is_zero
from odoo.exceptions import ValidationError
import json


class ProductProduct(models.Model):
    _inherit = 'product.product'

    def _change_standard_price(self, new_price, counterpart_account_id=False):
        """Helper to create the stock valuation layers and the account moves
        after an update of standard price.

        :param new_price: new standard price
        """
        # Handle stock valuation layers.
        svl_vals_list = []
        company_id = self.env.company
        for product in self:
            description = _('Product value manually modified (from %s to %s)') % (self.standard_price, new_price)
            svl_vals = product.with_context(new_price=new_price).split_layer_by_quant_location('change_price', description, company_id)
            svl_vals_list += svl_vals
        stock_valuation_layers = self.env['stock.valuation.layer'].sudo().create(svl_vals_list)

        # Handle account moves.
        product_accounts = {product.id: product.product_tmpl_id.get_product_accounts() for product in self}
        am_vals_list = []
        for stock_valuation_layer in stock_valuation_layers:
            product = stock_valuation_layer.product_id
            value = stock_valuation_layer.value
            if product.valuation != 'real_time':
                continue

            # Sanity check.
            if counterpart_account_id is False:
                raise UserError(_('You must set a counterpart account.'))
            if not product_accounts[product.id].get('stock_valuation'):
                raise UserError(
                    _('You don\'t have any stock valuation account defined on your product category. You must define one before processing this operation.'))

            if value < 0:
                debit_account_id = counterpart_account_id
                credit_account_id = product_accounts[product.id]['stock_valuation'].id
            else:
                debit_account_id = product_accounts[product.id]['stock_valuation'].id
                credit_account_id = counterpart_account_id

            move_vals = {
                'journal_id': product_accounts[product.id]['stock_journal'].id,
                'company_id': company_id.id,
                'ref': product.default_code,
                'stock_valuation_layer_ids': [(6, None, [stock_valuation_layer.id])],
                'line_ids': [(0, 0, {
                    'name': _('%s changed cost from %s to %s - %s') % (self.env.user.name, product.standard_price, new_price, product.display_name),
                    'account_id': debit_account_id,
                    'debit': abs(value),
                    'credit': 0,
                    'product_id': product.id,
                }), (0, 0, {
                    'name': _('%s changed cost from %s to %s - %s') % (self.env.user.name, product.standard_price, new_price, product.display_name),
                    'account_id': credit_account_id,
                    'debit': 0,
                    'credit': abs(value),
                    'product_id': product.id,
                })],
            }
            am_vals_list.append(move_vals)
        account_moves = self.env['account.move'].create(am_vals_list)
        if account_moves:
            account_moves.post()

        # Actually update the standard price.
        self.with_context(force_company=company_id.id).sudo().write({'standard_price': new_price})

        # Force update values because quant trigger compute_value after svl creation
        for stock_valuation_layer in stock_valuation_layers:
            qty_final_balance = 0.0
            total_cost_ending_balance = 0.0

            for quant_id in stock_valuation_layer.quant_ids:
                quant_id._compute_value()
                qty_final_balance += quant_id.quantity
                total_cost_ending_balance += quant_id.value

            stock_valuation_layer.qty_final_balance = qty_final_balance
            stock_valuation_layer.total_cost_ending_balance = total_cost_ending_balance
            stock_valuation_layer.unit_cost_final_balance = total_cost_ending_balance / qty_final_balance if qty_final_balance != 0 else 0.0

    @api.model
    def _svl_empty_stock(self, description, product_category=None, product_template=None):
        impacted_product_ids = []
        impacted_products = self.env['product.product']
        products_orig_quantity_svl = {}

        # get the impacted products
        domain = [('type', '=', 'product')]
        if product_category is not None:
            domain += [('categ_id', '=', product_category.id)]
        elif product_template is not None:
            domain += [('product_tmpl_id', '=', product_template.id)]
        else:
            raise ValueError()
        products = self.env['product.product'].search_read(domain, ['quantity_svl'])
        for product in products:
            impacted_product_ids.append(product['id'])
            products_orig_quantity_svl[product['id']] = product['quantity_svl']
        impacted_products |= self.env['product.product'].browse(impacted_product_ids)

        # empty out the stock for the impacted products
        empty_stock_svl_list = []
        for product in impacted_products:
            # FIXME sle: why not use products_orig_quantity_svl here?
            if float_is_zero(product.quantity_svl, precision_rounding=product.uom_id.rounding):
                # FIXME: create an empty layer to track the change?
                continue
            svsl_vals = product.split_layer_by_quant_location('out', description, self.env.company)
            empty_stock_svl_list += svsl_vals
        return empty_stock_svl_list, products_orig_quantity_svl, impacted_products

    def _svl_replenish_stock(self, description, products_orig_quantity_svl):
        refill_stock_svl_list = []
        for product in self:
            quantity_svl = products_orig_quantity_svl[product.id]
            if quantity_svl:
                svl_vals = product.split_layer_by_quant_location('in', description, self.env.company)
                refill_stock_svl_list += svl_vals
        return refill_stock_svl_list

    def split_layer_by_quant_location(self, type_layer, description, company):
        quant_ids = self.env['stock.quant'].search([('location_id.usage', '=', 'internal'), ('product_id', '=', self.id)])
        layer_data = []
        location_ids = quant_ids.mapped('location_id')
        for location in location_ids:
            quants_by_location = quant_ids.filtered(lambda x: x.location_id == location)
            if not quants_by_location:
                continue
            qty = 0.0
            quant_value = 0.0
            for quant in quants_by_location:
                qty += quant.quantity
                quant_value += quant.value

            if type_layer == 'in':
                new_data = self._prepare_in_svl_vals(qty, self.standard_price)
            elif type_layer == 'out':
                new_data = self._prepare_out_svl_vals(qty, company)
            else:
                new_price = self.env.context.get('new_price', False)
                if not new_price:
                    break
                if self.cost_method not in ('standard', 'average'):
                    continue
                quantity_svl = qty
                if float_is_zero(quantity_svl, precision_rounding=self.uom_id.rounding):
                    continue
                diff = new_price - self.standard_price
                value = company.currency_id.round(quantity_svl * diff)
                if company.currency_id.is_zero(value):
                    continue
                new_data = {
                    'product_id': self.id,
                    'value': value,
                    'quantity': 0
                }
            qty_final_balance = qty
            total_cost_ending_balance = quant_value
            unit_cost_final_balance = total_cost_ending_balance / qty_final_balance if qty_final_balance != 0 else 0.0

            new_data.update({
                'description': description,
                'company_id': company.id,
                'location_id': location.id,
                'qty_final_balance': qty_final_balance,
                'unit_cost_final_balance': abs(float('%.2f' % unit_cost_final_balance)),
                'total_cost_ending_balance': float('%.2f' % total_cost_ending_balance),
                'no_picking': True,
                'quant_ids': quants_by_location.ids
            })
            layer_data.append(new_data)
        return layer_data


class StockLocation(models.Model):
    _inherit = "stock.location"

    def _should_be_valued_internal(self):
        """ This method returns a boolean reflecting whether the products stored in `self` should
        be considered when valuating the stock of a company.
        """
        self.ensure_one()
        if self.usage == 'internal':
            return True
        return False


class StockValuationLayer(models.Model):
    _inherit = 'stock.valuation.layer'

    no_picking = fields.Boolean(
        string='Calculado fuera de picking',
        default=False
    )
    location_id = fields.Many2one(
        comodel_name='stock.location',
        string='Lugar'
    )
    qty_final_balance = fields.Float(string='Cantidad del saldo final')
    unit_cost_final_balance = fields.Float(string='Costo unitario del saldo final')
    total_cost_ending_balance = fields.Float(string='Costo total del saldo final')
    quant_ids = fields.Many2many(
        comodel_name='stock.quant',
        string='Quant'
    )

    @api.model_create_multi
    def create(self, values):
        for value in values:
            if 'rounding_adjustment' in value.keys():
                del value['rounding_adjustment']
        records = super(StockValuationLayer, self).create(values)

        for record in records:
            if record.stock_move_id and not record.no_picking:
                move = self.env['stock.move'].browse(record.stock_move_id.id)
                if move:
                    location_id, value = self.get_location_id(move, record)
                    quant_ids = self.env['stock.quant'].search([('location_id', '=', location_id.id), ('product_id', '=', record.product_id.id)])
                    qty_final_balance = 0.00
                    total_cost_ending_balance = 0.00
                    for quant in quant_ids:
                        qty_final_balance += quant.quantity
                        total_cost_ending_balance += quant.value
                    unit_cost_final_balance = total_cost_ending_balance / qty_final_balance if qty_final_balance != 0 else 0

                    record.write({
                        'location_id': location_id.id,
                        'qty_final_balance': qty_final_balance,
                        'unit_cost_final_balance': abs(float('%.2f' % unit_cost_final_balance)),
                        'total_cost_ending_balance': float('%.2f' % total_cost_ending_balance),
                    })
        return records

    def get_location_id(self, move, value):
        if move.location_id._should_be_valued_internal() and not move.location_dest_id._should_be_valued_internal():
            location_id = move.location_id
        elif not move.location_id._should_be_valued_internal() and move.location_dest_id._should_be_valued_internal():
            location_id = move.location_dest_id
        else:
            # _run_fifo_vacuum method use location 'in'
            location_id = move.location_dest_id
        return location_id, value

    @api.model
    def fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
        res = super(StockValuationLayer, self).fields_view_get(view_id=view_id, view_type=view_type, toolbar=toolbar, submenu=submenu)
        if view_type == 'tree':
            value = not self.env.user.has_group('valuation_layer_by_location.group_final_amount_warehouse')
            doc = etree.XML(res['arch'])
            fields = ['location_id', 'qty_final_balance', 'unit_cost_final_balance', 'total_cost_ending_balance']
            for field in fields:
                for node in doc.xpath("//field[@name='{}']".format(field)):
                    node.set("readonly", str(int(value)))
                    modifiers = json.loads(node.get("modifiers") or '{}')
                    modifiers['readonly'] = value
                    node.set("modifiers", json.dumps(modifiers))
            res['arch'] = etree.tostring(doc, encoding='unicode')
        return res
