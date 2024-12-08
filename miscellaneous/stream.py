import sys


class StdoutFilter:
    def __init__(self, std_out = sys.stdout, blacklist=[], whitelist=[], case_sensitive=False):
        self.std_out = std_out
        self.case_sensitive = case_sensitive
        self.blacklist = list(blacklist) if not case_sensitive else [word.lower() for word in blacklist]
        self.whitelist = list(whitelist) if not case_sensitive else [word.lower() for word in whitelist]
        
    def write(self, text):
        if self.filter(text):
            self.std_out.write(text)

    def flush(self):
        self.std_out.flush()

    def filter(self, text):
        words = text if self.case_sensitive else text.lower()

        if any(word in words for word in self.blacklist):
            return False

        if self.whitelist and not any(word in words for word in self.whitelist):
            return False

        return True




