class WalletError(Exception):
    status_code = 400
    detail = "Wallet error"


class WalletNotFound(WalletError):
    status_code = 404
    detail = "Wallet not found"


class InsufficientFunds(WalletError):
    status_code = 409
    detail = "Insufficient funds"


class BalanceOverflow(WalletError):
    status_code = 400
    detail = "Balance limit exceeded"
