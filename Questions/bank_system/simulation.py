"""
All your implementation code for the bank system simulation goes here.
"""
from dataclasses import dataclass
DAY = 86400000

@dataclass
class Account:
    id: str
    balance: int
    spending: int
    transactions: list
    payments: list

@dataclass
class Payment:
    id: str
    status: str
    amount: int
    timestamp: int


class Simulation:

    def __init__(self):
        self.accounts = {}
        self.total_withdraws = 0

    def _process_cashbacks(self, timestamp: int) -> None:
        for account_id in self.accounts:
            self.update_status(account_id, timestamp)

    def create_account(self, timestamp: int, account_id: str) -> bool | None:
        self._process_cashbacks(timestamp)
        if account_id in self.accounts:
            return False

        self.accounts[account_id] = Account(
            id=account_id,
            balance=0,
            spending=0,
            transactions=[[timestamp, 0]],
            payments=[]
        )
        return True

    def deposit(self, timestamp: int, account_id: str, amount: int) -> int | None:
        self._process_cashbacks(timestamp)
        if account_id not in self.accounts:
            return None

        account = self.accounts[account_id]
        account.balance += amount
        account.transactions.append([timestamp, amount])
        return account.balance

    def transfer(self, timestamp: int, source_account_id: str, target_account_id: str, amount: int) -> int | None:
        self._process_cashbacks(timestamp)
        if source_account_id not in self.accounts or target_account_id not in self.accounts:
            return None
        if source_account_id == target_account_id:
            return None

        source_account = self.accounts[source_account_id]
        target_account = self.accounts[target_account_id]

        if source_account.balance < amount:
            return None
        
        source_account.balance -= amount
        target_account.balance += amount

        source_account.spending += amount

        source_account.transactions.append([timestamp, -amount])
        target_account.transactions.append([timestamp, amount])

        return source_account.balance

    def top_spenders(self, timestamp: int, n: int) -> list[str] | None:
        self._process_cashbacks(timestamp)
        target_accounts = sorted(self.accounts.values(), key=lambda x: (-x.spending, x.id))[:n]

        res = []
        for account in target_accounts:
            res.append(f"{account.id}({account.spending})")
        return res

    def pay(self, timestamp: int, account_id: str, amount: int) -> str | None:
        self._process_cashbacks(timestamp)
        if account_id not in self.accounts:
            return None

        account = self.accounts[account_id]

        if account.balance < amount:
            return None

        account.balance -= amount
        account.spending += amount
        account.transactions.append([timestamp, -amount])

        self.total_withdraws += 1

        payment = Payment(
            id=f"payment{self.total_withdraws}",
            status="IN_PROGRESS",
            amount=amount,
            timestamp=timestamp + DAY
        )
        account.payments.append(payment)

        return payment.id

    def update_status(self, account_id: str, timestamp: int) -> None:
        account = self.accounts[account_id]
        i = 0
        while i < len(account.payments) and account.payments[i].timestamp <= timestamp:
            payment = account.payments[i]
            if payment.status == "CASHBACK_RECEIVED":
                i += 1
                continue

            cash_back = payment.amount * 2 // 100
            account.balance += cash_back
            account.transactions.append([payment.timestamp, cash_back])
            payment.status = "CASHBACK_RECEIVED"
            i += 1

    def get_payment_status(self, timestamp: int, account_id: str, payment: str) -> str | None:
        self._process_cashbacks(timestamp)
        if account_id not in self.accounts:
            return None

        account = self.accounts[account_id]
        current_payment = None
        for account_payment in account.payments:
            if account_payment.id == payment:
                current_payment = account_payment
                break

        if current_payment is None:
            return None

        return current_payment.status

    def merge_accounts(self, timestamp: int, account_id_1: str, account_id_2: str) -> bool | None:
        self._process_cashbacks(timestamp)
        if account_id_1 == account_id_2 or account_id_1 not in self.accounts or account_id_2 not in self.accounts:
            return False

        account_1 = self.accounts[account_id_1]
        account_2 = self.accounts[account_id_2]
        del self.accounts[account_id_2]

        account_1.balance += account_2.balance
        account_1.spending += account_2.spending
        account_1.transactions = sorted(account_1.transactions + account_2.transactions)
        account_1.payments = sorted(account_1.payments + account_2.payments, key=lambda x: x.timestamp)

        return True

    def get_balance(self, timestamp: int, account_id: str, time_at: int) -> int | None:
        self._process_cashbacks(timestamp)
        if account_id not in self.accounts:
            return None

        account = self.accounts[account_id]
        transactions = account.transactions

        if time_at < transactions[0][0]:
            return None

        total = 0

        for transaction in transactions:
            if transaction[0] <= time_at:
                total += transaction[1]
        return total
