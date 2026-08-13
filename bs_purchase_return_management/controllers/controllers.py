# from odoo import http


# class AsReturnManagement(http.Controller):
#     @http.route('/bs_purchase_return_management/bs_purchase_return_management', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/bs_purchase_return_management/bs_purchase_return_management/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('bs_purchase_return_management.listing', {
#             'root': '/bs_purchase_return_management/bs_purchase_return_management',
#             'objects': http.request.env['bs_purchase_return_management.bs_purchase_return_management'].search([]),
#         })

#     @http.route('/bs_purchase_return_management/bs_purchase_return_management/objects/<model("bs_purchase_return_management.bs_purchase_return_management"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('bs_purchase_return_management.object', {
#             'object': obj
#         })

