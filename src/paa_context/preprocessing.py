import unicodedata


def normalize(text):
    text = text.lower()

    text = unicodedata.normalize("NFD", text)
    text = "".join(
        c for c in text
        if unicodedata.category(c) != "Mn"
    )

    text = "".join(
        c if c.isalnum() else " "
        for c in text
    )

    return text.split()