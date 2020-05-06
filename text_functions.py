# coding: utf-8
import email
from email.iterators import typed_subpart_iterator
#
# Quelques fonctions de vérification de l'encodage de caractères utilisé dans le mail (au cas où) - Peut-être à supprimer (car double emploi)
#
def get_charset(message, default="ascii"):
    """Get the message charset"""

    if message.get_content_charset():
        return message.get_content_charset()

    if message.get_charset():
        return message.get_charset()

    return default


def get_body(message):
    """Get the body of the email message"""

    if message.is_multipart():
        # get the plain text version only
        text_parts = [part for part in typed_subpart_iterator(message, 'text', 'plain')]
        body = []
        for part in text_parts:
            charset = get_charset(part, get_charset(message))
            body.append(str(part.get_payload(decode=True), charset, "replace"))

        return u"\n".join(body).strip()

    else:  # if it is not multipart, the payload will be a string
        # representing the message body
        body = str(message.get_payload(decode=True), get_charset(message), "replace")
        return body.strip()

#
# Quelques fonctions de manipulation de chaînes de caractères
#

def conversion_accents(chaine):
    converter = {'é': 'e', 'è': 'e', 'ê': 'e', 'à': 'a', 'ç': 'c'}
    result = ""
    for c in chaine:
        if c in converter:
            c = converter[c]
        result += c
    return result
