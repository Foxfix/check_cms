#!/usr/bin/env python
# -*- coding: utf8 -*-
from flask import Flask, request
from detect_cms import CmsDetector


from flask_restful import Resource, Api

app = Flask(__name__)
api = Api(app)


class ForPortal(Resource):
    """
    Client POST the url and get the data in json format:
    url
    3 items for test on the portal
    type of site cms
    """
    def post(self, url):
        url = request.form['url']
        data = CmsDetector()
        url, info_tools, keywords, cms = data.detect(url)
        item_for_test = data.find_items_for_client_test(url, keywords[0])
        return {
                "url": url,
                "item_for_test": item_for_test,
                "cms": cms
        }


api.add_resource(ForPortal, '/<string:url>')

if __name__ == '__main__':
    app.run(port=4900, debug=False)
