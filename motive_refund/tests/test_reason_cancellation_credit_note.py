# coding: utf-8

from odoo.exceptions import AccessError
from odoo.tests.common import TransactionCase
from odoo.tests.common import Form


class TestReasonCancellation(TransactionCase):

    def setUp(self):
        super(TestReasonCancellation, self).setUp()
        self.reason_cancellation_model = self.env['reason.cancellation.credit.debit']
        self.res_users = self.env['res.users']
        self.account_invoice = self.env['account.move']
        # self.account_id = self.env['account.account'].search([('code', '=', '121100')])

        self.currency_id_usd = self.env['res.currency'].search([('name', '=', 'USD')])
        self.currency_id_pen = self.env['res.currency'].create({
            'name': 'SOL',
            'symbol': 'S/.'
        })
        self.journal_id_pen = self.env['account.journal'].create({
            'name': 'Diario Venta SOL- Prueba',
            'type': 'sale',
            'code': 'TestS',
            'sequence_number_next': 50,
            'currency_id': self.currency_id_pen.id
        })
        self.journal_id_usd = self.env['account.journal'].create({
            'name': 'Diario Venta USD- Prueba',
            'type': 'sale',
            'code': 'TestD',
            'sequence_number_next': 50,
            'currency_id': self.currency_id_usd.id
        })
        self.account_invoice_model = self.env['account.move']
        self.account_invoice_line_model = self.env['account.move.line']
        self.partner_id = self.env['res.partner'].create({
            'name': "partner1 ",
        })
        self.product_id = self.env['product.product'].create({
            'name': "producto1",
            'lst_price': 100
        })

    def create_reason_cancellation(self, code, description):
        reason = self.reason_cancellation_model.create({
            'code': code,
            'description': description,
        })
        return reason

    def create_res_users_by_group(self, groups, nro_user):
        user = self.res_users.create({
            'login': 'test_user%d' % nro_user,
            'name': 'Usuario%d - T' % nro_user,
            'email': 'usert%d@example.com' % nro_user,
            'notification_type': 'email',
            'groups_id': [(6, 0, groups)]
        })
        return user

    def create_invoice(self, type_invoice, invoice_amount, currency_id, journal_id):
        fmove = Form(
            self.env['account.move'].with_context(default_type=type_invoice)
        )
        fmove.partner_id = self.partner_id
        fmove.invoice_date = '2019-01-06'
        obj_invoice = fmove.save()
        with Form(obj_invoice) as obj_inv:
            with obj_inv.invoice_line_ids.new() as obj_line:
                obj_line.product_id = self.product_id
                obj_line.quantity = 3
                obj_line.price_unit = invoice_amount
                obj_line.account_id = self.env['account.account'].search([
                    ('user_type_id', '=', self.env.ref('account.data_account_type_revenue').id)
                ], limit=1)

        return obj_invoice

    def create_credit_note_from_wizard(self, invoice, filter, reason):
        context = {
            "active_model": 'account.move',
            "active_ids": [invoice.id],
            "active_id": invoice.id,
            'default_refund_method': filter,
            'default_date': "2019-01-31",
        }
        wizard = Form(
            self.env['account.move.reversal'].with_context(context),
            view='motive_refund.view_account_move_reversal_inherit'
        )
        wizard.reason_cancellation_id = reason
        return wizard.save()

    def test_01_create_reason_cancellation(self):
        reason = self.create_reason_cancellation(100, 'Gravado - Test')
        self.assertTrue(reason)
        print('------------TEST OK - CREATE------------')

    def test_02_reason_cancellation_permissions(self):
        document = self.create_reason_cancellation(100, 'Gravado - Test')
        group_account_invoice = self.env.ref('account.group_account_invoice')
        group_account_user = self.env.ref('account.group_account_user')
        group_account_manager = self.env.ref('account.group_account_manager')

        # set a different user(account role) to prove permissions
        invoice_account = self.create_res_users_by_group([group_account_invoice.id], 1)
        user_account = self.create_res_users_by_group([group_account_user.id], 2)
        manager_account = self.create_res_users_by_group([group_account_manager.id], 3)
        normal_account = self.create_res_users_by_group([], 4)

        # invoice_account user
        # should do
        document.with_user(invoice_account).read()
        # shouldn't do
        self.assertRaises(AccessError, document.with_user(invoice_account).write,
                          {'description': 'prueba - invoice account'})
        self.assertRaises(AccessError, document.with_user(invoice_account).unlink)

        print('------------TEST OK - INVOICE ACCOUNT------------')

        document = self.create_reason_cancellation(100, 'Gravado - Test')

        # user_account user
        # should do
        document.with_user(user_account).read()
        document.with_user(user_account).write({'description': 'prueba - user account'})
        document.with_user(user_account).unlink()

        print('------------TEST OK - USER ACCOUNT------------')

        document = self.create_reason_cancellation(100, 'Gravado - Test')

        # user_account user
        # should do
        document.with_user(manager_account).read()
        document.with_user(manager_account).write({'description': 'prueba - manager account'})
        document.with_user(manager_account).unlink()

        print('------------TEST OK - MANAGER ACCOUNT------------')

        # role different from account
        # should do
        document.with_user(normal_account).read()
        # shouldn't do
        self.assertRaises(AccessError, document.with_user(normal_account).write,
                          {'description': 'prueba - normal', 'code': 'ccc'})
        self.assertRaises(AccessError, document.with_user(normal_account).unlink)

        print('------------TEST OK - NORMAL USER------------')

    def test_03_create_credit_note_from_invoice(self):
        reason = self.create_reason_cancellation(100, 'Invoice - Debit - Test')
        invoice = self.create_invoice(
            type_invoice='out_invoice',
            invoice_amount=50,
            currency_id=self.currency_id_pen.id,
            journal_id=self.journal_id_pen.id
        )
        invoice.action_post()
        reason_name = "[%s] %s" % (reason.code, reason.description)

        wizard = self.create_credit_note_from_wizard(invoice, 'refund', reason)
        # test onchange method over description field on wizard
        self.assertEqual(wizard.reason, reason_name)
        print('------------TEST OK - ONCHANGE OVER DESCRIPTION(REFUND)------------')

        refund = wizard.reverse_moves()
        credit_note = False
        if refund.get('res_id'):
            credit_note = self.account_invoice.browse(refund['res_id'])
        elif refund.get('domain'):
            credit_note = self.account_invoice.search([('id', 'in', refund[0][2])])

        # check values passed from account.invoice.refund to account.invoice
        self.assertEqual(credit_note.name, reason_name)
        self.assertEqual(credit_note.reason_cancellation_id, reason)
        print('------------TEST OK - SET VALUES ACCOUNT INVOICE------------')
