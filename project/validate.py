import calendar
import hashlib
import os
import re
import time

ascii_pat = re.compile(r"^[\w_@\.]+$", re.ASCII)


class Validator:
    def __init__(self, data):
        self.errors = {}
        self.data = data

    def check(self, field, validator, not_null=True):
        val = self.data.get(field, None)
        if not val:
            if not_null:
                self.errors[field] = f"{field} cannot be empty"
        else:
            try:
                # print(f"{validator}: ->{val}<-")
                val = globals()[validator](val)
            except (TypeError, ValueError) as err:
                # print(err)
                self.errors[field] = str(err)
        return val

    @property
    def is_ok(self):
        return len(self.errors) == 0

    def error_list(self):
        return [f"{k}: {v}" for k, v in self.errors.items()]


def is_string(s):
    if not isinstance(s, str):
        raise TypeError(
            "`{}` must be string or unicode, {} found".format(name, type(s).__name__)
        )
    return s


def ascii_string(s, prop="", lang="en"):
    if hasattr(prop, "_name"):
        name = prop._name
    else:
        name = str(prop)
    if not isinstance(s, str):
        raise TypeError(
            "`{}` must be string or unicode, {} found".format(name, type(s).__name__)
        )
    if len(s) < 4:
        raise ValueError(msg("almeno_4", lang) % name)
    if not ascii_pat.match(s):
        raise ValueError(msg("solo_lettere_e_numeri", lang) % name)
    return s


def email(email):
    eml = re.compile("^[a-zA-Z0-9-_.]+@[a-zA-Z0-9-_.]+[.][a-zA-Z0-9-_.]+$")
    m = eml.match(email)
    if m:
        return m.group()
    else:
        raise ValueError("`%s` doesn't look like an email address." % email)


def password(val: str) -> str:
    """
    Validates a password string.
    Raises ValueError with a specific message if validation fails.
    Returns the original string if it passes all checks.
    """

    if not val:
        raise ValueError("Password cannot be empty.")

    if len(val) < 8:
        raise ValueError("Password must be at least 8 characters long.")

    if not any(char.isupper() for char in val):
        raise ValueError("Password must contain at least one uppercase letter.")

    if not any(char.isdigit() for char in val):
        raise ValueError("Password must contain at least one number.")

    if not any(not char.isalnum() for char in val):
        raise ValueError("Password must contain at least one special character.")

    return val


def hash(s, prop=""):
    if hasattr(prop, "_name"):
        name = prop._name
    else:
        name = str(prop)
    val = ascii_string(s, name)
    val = hashlib.sha1(val.encode("utf-8")).hexdigest()
    return val


def phash(password, salt=None, name=""):
    password = ascii_string(password, name)
    if not salt:
        salt = os.urandom(32)
    key = hashlib.pbkdf2_hmac(
        "sha256",  # The hash digest algorithm for HMAC
        password.encode("utf-8"),  # Convert the password to bytes
        salt,  # Provide the salt
        100000,  # It is recommended to use at least 100,000 iterations of SHA-256
    )
    hash_pw = salt + key
    return hash_pw


def date(s, date_name):
    """
    Controlla che la stringa in input sia una data valida

    Restituisce una data nel formato aaaa-mm-gg
    """
    _s = s
    s = s.replace(".", " ")
    s = s.replace("/", " ")
    s = s.replace("-", " ")
    s = s.replace(",", " ")
    s = s.split()

    # per essere una data valida deve avere 2 o 3 elementi
    if len(s) not in (2, 3):
        raise ValueError("{}: -1- invalid date `{}`".format(date_name, _s))

    # gli elementi che compongono la data devono essere numerici
    for elem in s:
        if not elem.isdigit():
            raise ValueError("{}: -2- not numeric value `{}`".format(date_name, _s))

    # il mese deve essere compreso fra 1 e 12
    mese = int(s[1])
    if mese not in (1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12):
        raise ValueError("{}: -4- invalid month `{}`".format(date_name, _s))

    # Se ci sono due elementi allora deve essere del tipo gg mm
    # e gg + mm + anno corrente deve essere una data valida
    if len(s) == 2:
        # In questo caso gli elementi che compongono la stringa non
        # devono essere piu' lunghi di due caratteri
        for elem in s:
            if len(elem) > 2:
                raise ValueError("{}: -3- invalid date `{}`".format(date_name, _s))

        # Il giorno deve essere un giorno del mese
        anno_corrente = time.localtime(time.time())[0]
        anno = anno_corrente
        giorno = int(s[0])
        if giorno > calendar.monthrange(anno_corrente, mese)[1]:
            raise ValueError("{}: -5- invalid day `{}`".format(date_name, _s))

        # Ritorna la data in formato "aaaa-mm-gg"
        result = str(anno) + "-" + str(mese).zfill(2) + "-" + str(giorno).zfill(2)
        return result

    # Da qui' sono nel caso in cui e' stata inserita una data nei formati:
    # --> aaaa mm gg
    # --> gg mm aaaa
    # gli altri formati vengono segnalati come errore
    if len(s[0]) == 4:  # suppongo di essere nel formato aaaa mm gg
        anno = int(s[0])
        giorno = int(s[2])
    elif len(s[2]) == 4:  # suppongo di essere nel formato gg mm aaaa
        anno = int(s[2])
        giorno = int(s[0])
    else:
        raise ValueError("{}: -6- invalid date `{}`".format(date_name, _s))

    if anno < 1900 or anno > 2100:
        raise ValueError("{}: -7- invalid year `{}`".format(date_name, _s))

    if giorno > calendar.monthrange(anno, mese)[1]:
        raise ValueError("{}: -8- invalid day `{}`".format(date_name, _s))

    # Ritorna la data in formato "aaaa-mm-gg"
    result = str(anno) + "-" + str(mese).zfill(2) + "-" + str(giorno).zfill(2)
    return result


def to_int(value, property_name="", lang="en"):
    """Validate integer property.

    Returns:
            A valid value.

    Raises:
            ValueError if value is not an integer or long instance.
    """
    if value is None:
        return value
    try:
        value = int(value)
    except:
        raise ValueError(msg("intero", lang) % property_name)
    if not isinstance(value, int) or isinstance(value, bool):
        raise ValueError(msg("intero", lang) % property_name)
    if value < -0x8000000000000000 or value > 0x7FFFFFFFFFFFFFFF:
        raise ValueError(msg("troppo_lungo", lang) % property_name)
    return value


def to_float(value, property_name):
    """Validate float property.

    Returns:
            A valid value.

    Raises:
            ValueError if value is not float instance.
    """
    if value is None:
        return value
    try:
        value = float(value)
    except:
        raise ValueError(
            "Property %s must be float, not a `%s`"
            % (property_name, type(value).__name__)
        )
    if (
        not isinstance(value, float)
        or isinstance(value, int)
        or isinstance(value, bool)
    ):
        raise ValueError(
            "Property %s must be float, not a %s"
            % (property_name, type(value).__name__)
        )
    return value


def msg(msg_code, lang):
    if lang not in ("en", "it"):
        lang = "en"
    dict = {
        "almeno_4": {
            "en": "`%s` must be at least four characters long.",
            "it": "`%s` dovrebbe essere di almeno 4 lettere.",
        },
        "solo_lettere_e_numeri": {
            "en": "Please, for `%s` try to use only letters, numbers or `_`,`.`",
            "it": (
                "Qualcosa non va in `%s`, prova ad usare solo lettere numeri o i"
                " caratteri `_`,`.`"
            ),
        },
        "intero": {
            "en": "%s must be int or long",
            "it": "%s non sembra essere un numero intero",
        },
        "troppo_lungo": {
            "en": "Property %s must fit in 64 bits",
            "it": "%s e` veramente troppo grande come numero",
        },
    }
    return dict[msg_code][lang]


if __name__ == "__main__":
    ll = [
        "pippo",
        "pluto",
        "paperino",
        "al",
        ("l",),
        "pi.p_po",
        "pl?uto",
        "pàperino",
        "capp@",
        (
            "kjfrlkerwhflkqerhfqkerfhqlekrfhqelkrfhqlekrfhlqkerfskfjhlkwehflksjdfhsadlkfhaslkdfhslakdfhaldks"
            " asdfsldkah skdhf "
        ),
    ]
    start = time.time()
    for item in ll:
        try:
            ascii_string(item, "test")
        except Exception as err:
            print(item, str(err))
        else:
            print(item, "ok!")
    stop = time.time()
    t1 = repr(stop - start)[0:5]
