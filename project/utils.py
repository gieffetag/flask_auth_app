import binascii
import glob
import html
import os
import pprint
import re
import stat
import subprocess
import time
import unicodedata
import urllib.parse
import uuid
from collections import defaultdict
from configparser import ConfigParser

try:
    unicode
    basestring
except NameError:
    unicode = str
    basestring = str


def get_token():
    return binascii.b2a_hex(uuid.uuid4().bytes).decode("utf-8")


def get_secret():
    x = binascii.b2a_base64(uuid.uuid4().bytes) + binascii.b2a_base64(
        uuid.uuid4().bytes
    )
    return x.decode("utf-8")


def sleep_or_exit(sec=10):
    exit = False
    print()
    print("Sleeping for %s secs, ctrl+c for break" % sec)
    try:
        time.sleep(sec)
    except KeyboardInterrupt:
        print("Program exits!")
        exit = True
    return exit


def load_config(filename, section="", uppercase=True):
    """
    Loads a configuration .ini file, and then pulls out the 'section' key
    to make a configuration dictionary.
    """
    config = ConfigParser()
    if uppercase:
        config.optionxform = str.upper  # all keys will be uppercase
    config_file = open(filename)
    config.readfp(config_file)
    if not section:  # Load all sections (duplicate option key will be lost!)
        result = {}
        sections = config.sections()
        for section in sections:
            result.update(dict(config.items(section)))
    else:
        result = dict(config.items(section))
    return result


def find_free_name(filename, filelist):
    suffix = 0
    base, ext = os.path.splitext(filename)
    while 1:
        if filename not in filelist:
            return filename
        suffix += 1
        filename = base + "_" + str(suffix) + ext


def check_osx_location(location="Casa Airport"):
    """Return true if `location` is the name of actual selected network."""
    pat = re.compile(r"^\s*\*.*\(%s\)" % location, re.M)
    buf = subprocess.getoutput("/usr/sbin/scselect")
    if pat.search(buf):
        return True
    else:
        return False


def dict_to_table(dict_list, field_list=[], result_type=""):
    if field_list == []:
        field_list = list(dict_list[0].keys())
    elif isinstance(field_list, str):
        field_list = [el.strip() for el in field_list.split(",")]

    l = []
    l.append("\t".join(field_list))
    for d in dict_list:
        ll = []
        for key in field_list:
            d[key] = d.get(key, "")
            if d[key] == None:
                d[key] = ""
            try:
                s = str(d[key])
            except UnicodeEncodeError:
                s = d[key].encode("utf8", "replace")
            ll.append(s)
        l.append("\t".join(ll))

    if result_type == "ftext":
        return table_to_text(l)
    else:
        return "\n".join(l)


def table_to_text(ll):
    """Data una lista di righe con i campi separati da tabulatori
    restitusce un testo formattato tipo query "mysql"
    """
    column_lenght_dict = {}
    for line in ll:
        llc = line.split("\t")
        i = 0
        for col in llc:
            column_lenght_dict[i] = column_lenght_dict.get(i, 2)
            column_lenght_dict[i] = max(column_lenght_dict[i], len(col) + 2)
            i += 1
    sep = ["+"]
    for i in range(len(ll[0].split("\t"))):
        sep.append("-" * column_lenght_dict[i])
        sep.append("+")
    sep = "".join(sep)
    t = [sep]
    j = 0
    for line in ll:
        llc = line.split("\t")
        i = 0
        tl = ["|"]
        for col in llc:
            tl.append(" %s |" % col.ljust(column_lenght_dict[i] - 2))
            i += 1
        tl = "".join(tl)
        t.append(tl)
        if j == 0 or j == (len(ll) - 1):
            t.append(sep)
        j += 1
    return "\n".join(t)


def dump(values):
    return "<pre>%s</pre>" % pprint.pformat(values)


def set_proxy(verbose=False):
    http_proxy = https_proxy = "http://proxy.mmfg.it:8080"
    os.environ["http_proxy"] = http_proxy
    os.environ["https_proxy"] = https_proxy
    if verbose:
        print("http_proxy = %s" % http_proxy)
        print("https_proxy = %s" % https_proxy)


def sib_path(filename, name):
    """Generate a path that is a sibling of filename."""
    return os.path.join(os.path.dirname(filename), name)


def cgi_escape(value):
    if isinstance(value, list):
        value = [html.escape(x) for x in value]
    elif isinstance(value, dict):
        value = {
            k: html.escape(value[k]) if isinstance(value[k], basestring) else value[k]
            for k in list(value.keys())
        }
    else:
        value = html.escape(value)
    return value


def check_dir(dir_name, keep_clean=False):
    ## Controlla se esiste la directory
    if os.path.exists(dir_name):
        if os.path.isdir(dir_name):
            pass
        else:
            os.remove(dir_name)
            os.mkdir(dir_name)
    else:
        os.mkdir(dir_name)

    if keep_clean:
        ## Cancella i file piu' vecchi di un giorno
        for fn in glob.glob(dir_name + "/*"):
            if os.stat(fn)[stat.ST_MTIME] < (time.time() - 86400):
                os.remove(fn)


def cgi_params(pard, param, defdict=False):
    """
    Estrapola dal pard le chiavi del tipo `param`[chiave] e le restituisce
    in un nuovo dizionario.

    Esempio:
            >>> pard = {'pippo': 'pluto', 'p[k]': 3, 'p[a2l]': 'paperino'}
            >>> d = cgi_params(pard, 'p')
            >>> d
            {'k': 3, 'a2l': 'paperino'}

    """
    pat = re.compile(r"%s\[(\w+)\]" % param)
    result = defaultdict(str) if defdict else {}
    for k in pard:
        g = pat.match(k)
        if g:
            result[g.group(1)] = pard[k]
    return result


def remove_accents(input_str):
    nkfd_form = unicodedata.normalize("NFKD", input_str)
    nkfd_form = nkfd_form.replace("\u0300", "`").replace("\u0301", "'")
    return "".join([c for c in nkfd_form if not unicodedata.combining(c)])


def compare_hashes(a, b):
    """Checks if two hash strings are identical.

    The intention is to make the running time be less dependant on the size of
    the string.

    :param a:
            String 1.
    :param b:
            String 2.
    :returns:
            True if both strings are equal, False otherwise.
    """
    if len(a) != len(b):
        return False

    result = 0
    for x, y in zip(to_basestring(a), to_basestring(b)):
        result |= ord(x) ^ ord(y)

    return result == 0


class SimpleTotal(dict):
    def __missing__(self, key):
        return 0

    def inc(self, key):
        self[key] += 1

    def list(self):
        l = ["%s: %s" % item for item in list(self.items())]
        return l


class ExecTime:
    def __init__(self, name=""):
        self.start = time.time()
        self.name = name

    def exec_time(self, msg="", reset=True):
        stop = time.time()
        result = " ".join(
            [
                "\033[0;31m",  # Red
                "Exec Time:",
                "\033[0m",  # No Color
                self.name,
                msg,
                repr(stop - self.start)[:5],
            ]
        )
        if reset:
            self.start = time.time()
        return result


def today():
    return time.strftime("%Y-%m-%d", time.localtime())


def now():
    return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())


def digit_to_char(digit):
    if digit < 10:
        return str(digit)
    return chr(ord("a") + digit - 10)


def str_base(number, base):
    if number < 0:
        return "-" + str_base(-number, base)
    (d, m) = divmod(number, base)
    if d > 0:
        return str_base(d, base) + digit_to_char(m)
    return digit_to_char(m)


def get_alpha_token():
    x = binascii.b2a_hex(uuid.uuid4().bytes)
    n = int(x, 16)
    return str_base(n, 36)


def to_utf8(value):
    """Converts a string argument to a byte string.
    If the argument is already a byte string or None, it is returned unchanged.
    Otherwise it must be a unicode string and is encoded as utf8.
    """
    if isinstance(value, (bytes, type(None))):
        return value
    if not isinstance(value, str):
        raise TypeError("Expected bytes, unicode, or None; got %r" % type(value))
    return value.encode("utf-8")


def to_basestring(value):
    """Converts a string argument to a subclass of basestring.

    This comes from `Tornado`_.

    In python2, byte and unicode strings are mostly interchangeable,
    so functions that deal with a user-supplied argument in combination
    with ascii string constants can use either and should return the type
    the user supplied.	In python3, the two types are not interchangeable,
    so this method is needed to convert byte strings to unicode.
    """
    if isinstance(value, str):
        return value
    if not isinstance(value, bytes):
        raise TypeError("Expected bytes, unicode, or None; got %r" % type(value))
    return value.decode("utf-8")


def dot_env():
    """
    Aggiunge alle variabili d'ambiente le variabili contenute
    nel file ".env" (se esite)
    """
    env = {}
    if os.path.isfile(".env"):
        fp = open(".env")
        for line in fp.readlines():
            if line[0] == "#":
                continue
            if line[-1] == "\n":
                line = line[:-1]
            if not line:
                continue
            key, value = line.split("=")
            env[key] = value
        fp.close()
    os.environ.update(env)


# def url_to_link(s, tag=None):
#     pat = re.compile(r"(https?:\/\/[^\s]+)")
#     if tag:
#         res = pat.sub(f"<{tag}>\\1</{tag}>", s)
#     else:
#         res = pat.sub(r'<a href="\1" target="_blank">\1</a>', s)
#     return res


def url_to_link(s, tag=None, localdomains=None):
    pat = re.compile(
        r"(?<!href=[\"'])(?!(?:(?!<code>).)*<\/code>)(https?://[^\s<\"']+)"
    )
    if tag:
        res = pat.sub(f"<{tag}>\\1</{tag}>", s)
    else:
        res = url_replace(s, pat, localdomains)
    return res


def url_replace(s, pat, localdomains=None):
    if not localdomains:
        localdomains = []
    if not isinstance(localdomains, (list, tuple)):
        raise ValueError("localdomains must be list or tuple")
    res = ""
    pos = 0
    for match in pat.finditer(s):
        res += s[pos : match.start()]
        url = match.group(1)
        url_parse = urllib.parse.urlparse(url)
        if url_parse.netloc in localdomains or not localdomains:
            link = f'<a href="{url}">{url}</a>'
        else:
            link = f'<a href="{url}" target="_blank" rel="noreferrer">{url}</a>'
        res += link
        pos = match.end()
    res += s[pos:]
    return res


def tag_to_link(s, tag="url", localdomains=None):
    pat = re.compile(f"<{tag}>(.*?)</{tag}>")
    res = url_replace(s, pat, localdomains)
    return res


def format_as_pre(s):
    s = url_to_link(s, "url")
    s = s.replace("\n", "<br>")
    s = s.replace("\t", "&nbsp;" * 4)
    s = s.replace(" ", "&nbsp;")
    s = tag_to_link(s, "url")
    return s
