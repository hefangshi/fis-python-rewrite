import unittest
import os
import sys

lib_path = os.path.normpath(os.path.join(os.path.dirname(__file__) + '/../'))
sys.path.append(lib_path)

from rewrite import Rewrite
import json

class MockRequestHandler:

    def __init__(self):
        self.content = ''
        self.headers = {}
        self.request = {
            "headers" : {}
        }

    def write(self, content):
        self.content = self.content + content

    def redirect(self, url):
        self.direct = url

    def set_header(self, name, value):
        self.headers[name] = value

    def set_status(self, status):
        self.headers['Status'] = status


class test_rewrite_function(unittest.TestCase):

    def setUp(self):
        self.handler = MockRequestHandler()
        self.rewrite = Rewrite(self.handler)
        self.rewrite.root = os.path.join(os.path.dirname(__file__), 'testdata')

    def test_inner_predefine(self):
        self.assertEqual(self.rewrite.get_mime('.js'), 'text/javascript')

    def test_init_define(self):
        self.rewrite = Rewrite(self.handler, mime={'.js': 'something else'})
        self.assertEqual(self.rewrite.get_mime('.js'), 'something else')

    def test_predefine(self):
        self.assertEqual(self.rewrite.get_mime('.bmp'), 'image/x-ms-bmp')

    def test_none_define(self):
        self.assertEqual(self.rewrite.get_mime('.kkk'), 'application/x-kkk')

    def test_rewrite_callback(self):
        callbacked = [False]
        def callback(url):
            callbacked[0] = True
            self.assertEqual(url, 'test?param=1')
        self.rewrite.add_rewrite_callback('test', callback)
        self.assertEqual(self.rewrite.match('test?param=1'), True)
        self.assertEqual(callbacked[0], True)

    def test_rewrite_callback_fail(self):
        callbacked = [False]
        def callback(url):
            callbacked[0] = True
            self.assertEqual(url, 'test?param=1')
        self.rewrite.add_rewrite_callback('test1', callback)
        self.assertEqual(self.rewrite.match('test?param=1'), False)
        #never call back
        self.assertEqual(callbacked[0], False)

    def test_get_confs(self):
        expect = [os.path.normpath(os.path.join(self.rewrite.root, 'server-conf/test.conf'))]
        conf_path = os.path.normpath(os.path.join(self.rewrite.root, 'server-conf/'))
        self.assertEqual(self.rewrite.get_confs(conf_path), expect)

    def test_get_rulers(self):
        expect = [
            {
                "type" : "rewrite",
                "rewrite" : "/test/data/test.py",
                "rule" : "^runpytest"
            },{
                "type" : "redirect",
                "rewrite" : "/runpytest?from=redirect",
                "rule" : "^redirec.*est"
            }
        ]
        self.assertEqual(self.rewrite.get_rulers(), expect)

    def test_redirect(self):
        self.assertEqual(self.rewrite.match('redirecttest'), True)
        self.assertEqual(self.handler.direct, '/runpytest?from=redirect')

    def test_rewrite_py(self):
        self.assertEqual(self.rewrite.match('runpytest'), True)
        actual = json.loads(self.handler.content)
        self.assertEqual(self.handler.headers['Content-Type'], 'application/json')
        self.assertEqual(actual['user'], 'hefangshi')

if __name__ == '__main__':
    unittest.main()
