class URL(str):
    def __init__(self, base_url, sep="/"):
        self.sep = sep
        self.base_url = str(base_url).strip(self.sep)

    def __eq__(self, other):
        if isinstance(other, str):
            other = URL(other)
        if isinstance(other, URL):
            return self.base_url == other.base_url
        return False

    def __ne__(self, other):
        if isinstance(other, str):
            other = URL(other)
        if isinstance(other, URL):
            return self.base_url != other.base_url
        return False

    def __truediv__(self, other):
        other = str(other).strip(self.sep)
        return URL(self.base_url + self.sep + other)

    def __str__(self):
        return self.base_url