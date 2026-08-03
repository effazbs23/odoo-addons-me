# from odoo import http


# class AsReturnManagement(http.Controller):
#     @http.route('/as_return_management/as_return_management', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/as_return_management/as_return_management/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('as_return_management.listing', {
#             'root': '/as_return_management/as_return_management',
#             'objects': http.request.env['as_return_management.as_return_management'].search([]),
#         })

#     @http.route('/as_return_management/as_return_management/objects/<model("as_return_management.as_return_management"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('as_return_management.object', {
#             'object': obj
#         })

