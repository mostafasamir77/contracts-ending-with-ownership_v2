{
    'name': "Contracts ending with ownership",
    'author': "elsasa",
    'version': '18.1',
    'depends': ['base', 'contacts', 'mail', 'stock', 'accountant','hr','fleet'],
    'data': [
        'security/ir.model.access.csv',
        'data/sequence.xml',
        'views/base_view.xml',
        'views/res_partner_view.xml',
        'views/stock_location_inherit_view.xml',
        'views/fleet_vehicle_state_inherit_view.xml',
        'views/contract_div_view.xml',
        'views/ware_house_inherit_view.xml',
        # 'views/customer_view.xml',
        'views/contract_view.xml',
        'views/customer_menu.xml',
        'views/payment_menu.xml',
        'views/installments_view.xml',
        'views/other_charge_view.xml',
        'views/guarantors_view.xml',
        'wizard/contract_buttons_wizard_view.xml',
    ],
    'assets': {
        'web.assets_backend' : ['contracts_ending_with_ownership/static/src/css/contract.css']
    },
    'application': True,
}