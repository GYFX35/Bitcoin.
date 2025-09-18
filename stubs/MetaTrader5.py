def initialize():
    return True

def account_info():
    class AccountInfo:
        def _asdict(self):
            return {
                'login': 12345,
                'balance': 10000.0,
            }
    return AccountInfo()

def shutdown():
    pass

def last_error():
    return ""
