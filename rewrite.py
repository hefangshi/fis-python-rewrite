import os
import mimetypes
import re
import sys

lib_path = os.path.normpath(os.path.join(os.path.dirname(__file__), '../'))
sys.path.append(lib_path)

class Rewrite():

    """fis rewrite class"""
    def __init__(self, handler, **kwargs):
        self.handler = handler
        self.root = os.path.normpath(os.path.join(os.path.dirname(__file__), '../../'))
        self.mime =  mimetypes.types_map
        self.predefine_rules = {}
        self.accept_rule_types = ['rewrite', 'redirect']
        self.init_mime()
        if 'root' in kwargs:
            self.root = kwargs['root']
        if 'mime' in kwargs:
            # merge mime config
            self.mime.update(kwargs['mime'])

    def init_mime(self):
        mime = {
            '.js' : 'text/javascript',
            '.json' : 'application/json',
            '.mocha' : 'text/javascript',
            '.svg' : 'image/svg+xml',
        }
        self.mime.update(mime)

    def get_mime(self, ext):
        if ext in self.mime:
            return self.mime[ext]
        else:
            return 'application/x-' + ext[1:]

    def add_rewrite_callback(self, ruler, callback):
        self.predefine_rules[ruler.lower()] = callback

    def get_confs(self, path):
        confs = []
        path = os.path.normpath(path)
        if os.path.exists(path) == False:
            return confs;
        files = os.listdir(path)
        for file_name in files:
            file_name = os.path.normpath(path + '/' +file_name)
            if os.path.isfile(file_name):
                if file_name == 'common.conf':
                    #TODO: why insert to first
                    confs.insert(0, file_name)
                else:
                    confs.append(file_name)
        return confs;

    def match(self, url):
        rules = self.get_rulers()
        for rule in rules:
            match = re.match(rule['rule'], url)
            if match is None:
                continue
            func_name = 'rule_' + rule['type'] + '_handler'
            func = getattr(self, func_name)
            if func:
                func(url, rule)
                return True
            else:
               raise TypeError("invalid rule type: %s", rule['type'])
        return False

    def rule_redirect_handler(self, url, rule):
        self.handler.redirect(rule['rewrite'])

    def rule_rewrite_handler(self, url, rule):
        if len(rule['rewrite']) > 1 and (rule['rewrite'][0] == '/' or rule['rewrite'][0] == '\\'):
            rule['rewrite'] = rule['rewrite'][1:]
        path = os.path.join(self.root, rule['rewrite'])
        if not (path + os.path.sep).startswith(self.root):
            self.handler.set_status(403)
            return        
        file_name, file_ext = os.path.splitext(path)
        if file_ext == '.py':
            local = {'handler' : self.handler}
            execfile(path, {}, local)
        else:
            static = StaticFileHandler()
            static.serve_static_file(self.handler, path)

    def rule_function_handler(self, url, rule):
        rule['rewrite'](url)

    def get_rulers(self):
        conf_path = os.path.normpath(os.path.join(self.root, 'server-conf/'))
        confs = self.get_confs(conf_path)
        rules = []
        for conf in confs:
            handle = open(conf, "r")
            for line in handle:
                rule_tokens = re.split('\s+', line.strip())
                if len(rule_tokens) is not 3:
                    continue
                if rule_tokens[0] not in self.accept_rule_types:
                    continue
                rule = {
                    'rule' : rule_tokens[1],
                    'rewrite' : rule_tokens[2],
                    'type' : rule_tokens[0],
                }
                rules.append(rule)
            handle.close()
        #user defined rulers has higher priority than predefined rulers
        for rule in self.predefine_rules:
            rule = {
                'rule' : rule,
                'rewrite' : self.predefine_rules[rule],
                'type' : 'function'
            }
            rules.append(rule)
        return rules


#from tornado
class StaticFileHandler():

    def serve_static_file(self, handler, path):
        import datetime, time, hashlib
        import email
        abspath = path
        # os.path.abspath strips a trailing /
        # it needs to be temporarily added back for requests to root/
        if not os.path.exists(abspath):
            handler.set_status(404)
            return
        if not os.path.isfile(abspath):
            handler.set_status(403)
            return

        stat_result = os.stat(abspath)
        mtime = int(stat_result.st_mtime)
        modified = datetime.datetime.fromtimestamp(mtime)

        handler.set_header("Last-Modified", modified)

        mime_type, encoding = mimetypes.guess_type(abspath)
        if mime_type:
            handler.set_header("Content-Type", mime_type)

        cache_time = 86400 * 365 * 10

        if cache_time > 0:
            handler.set_header("Expires", datetime.datetime.utcnow() +
                                       datetime.timedelta(seconds=cache_time))
            handler.set_header("Cache-Control", "max-age=" + str(cache_time))
        else:
            handler.set_header("Cache-Control", "public")

        # Check the If-Modified-Since, and don't send the result if the
        # content has not been modified
        ims_value = handler.request.headers.get("If-Modified-Since")
        if ims_value is not None:
            date_tuple = email.utils.parsedate(ims_value)
            if_since = datetime.datetime.fromtimestamp(time.mktime(date_tuple))
            if if_since >= modified:
                handler.set_status(304)
                return

        with open(abspath, "rb") as file:
            data = file.read()
            hasher = hashlib.sha1()
            hasher.update(data)
            handler.set_header("Etag", '"%s"' % hasher.hexdigest())
            handler.write(data)
            handler.set_header("Content-Length", len(data))