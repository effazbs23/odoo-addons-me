# -*- coding: utf-8 -*-
import json

from odoo import api, fields, models


class BlogBlog(models.Model):
    _inherit = 'blog.blog'

    @api.model
    def kingdom_get_column_posts(self, blog_hint=None, limit=3, exclude_blog_id=None):
        """Published posts for a homepage blog/news column."""
        domain = [
            ('active', '=', True),
            ('website_published', '=', True),
            ('post_date', '<=', fields.Datetime.now()),
        ]
        blog = self.browse()
        if blog_hint:
            blog = self.sudo().search([('name', 'ilike', blog_hint)], limit=1)
        if not blog:
            blogs = self.sudo().search([], order='sequence asc, id asc')
            if blog_hint and blog_hint.lower() == 'news' and len(blogs) > 1:
                blog = blogs[1]
            elif blogs:
                blog = blogs[0]
        if blog:
            domain.append(('blog_id', '=', blog.id))
        if exclude_blog_id:
            domain.append(('blog_id', '!=', exclude_blog_id))
        posts = self.env['blog.post'].sudo().search(
            domain,
            order='post_date desc, id desc',
            limit=limit,
        )
        return posts, blog

    def kingdom_list_url(self):
        self.ensure_one()
        return '/blog/%s' % self.env['ir.http']._slug(self)


class BlogPost(models.Model):
    _inherit = 'blog.post'

    def kingdom_cover_image_url(self):
        self.ensure_one()
        try:
            props = json.loads(self.cover_properties or '{}')
            background = props.get('background-image', '')
            if background.startswith('url('):
                return background[4:-1].strip("'\"")
        except (TypeError, ValueError, json.JSONDecodeError):
            pass
        return '/website_blog/static/src/img/blog_1.jpeg'

    def kingdom_cover_image_style(self):
        self.ensure_one()
        url = self.kingdom_cover_image_url()
        return 'background-image: url(%s);' % url

    def kingdom_formatted_post_date(self):
        self.ensure_one()
        if not self.post_date:
            return ''
        post_dt = fields.Datetime.context_timestamp(self, self.post_date)
        return post_dt.strftime('%B %d, %Y')

    def kingdom_comment_count(self):
        self.ensure_one()
        return len(self.website_message_ids)
