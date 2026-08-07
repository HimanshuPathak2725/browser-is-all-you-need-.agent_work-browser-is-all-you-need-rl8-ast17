"""Owner source for the three CHARM V1 Bank Account tasks."""

from __future__ import annotations

from scripts.charm_v1_topics.common import package, prompt, support


LEDGER_HEADER = r'''#pragma once
#include <limits>
#include <set>
#include <string>
#include <utility>
#include <vector>
namespace charm::bank {
class CentLedger {
public:
    bool apply(std::string id, long long delta) {
        if (id.empty() || seen_.count(id) != 0U) return false;
        if ((delta > 0 && balance_ > std::numeric_limits<long long>::max() - delta) ||
            (delta < 0 && balance_ < std::numeric_limits<long long>::min() - delta)) return false;
        const long long next = balance_ + delta;
        if (next < 0) return false;
        balance_ = next;
        seen_.insert(id);
        accepted_.push_back(std::move(id));
        return true;
    }
    long long balance() const { return balance_; }
    std::vector<std::string> accepted_ids() const { return accepted_; }
private:
    long long balance_ = 0;
    std::set<std::string> seen_;
    std::vector<std::string> accepted_;
};
}
'''

LEDGER_START = r'''#pragma once
#include <string>
namespace charm::bank {
class CentLedger {
public:
    bool apply(std::string id, long long delta);
    long long balance() const;
    std::vector<std::string> accepted_ids() const;
};
}
'''

LEDGER_TEST = r'''#include "idempotent-cent-ledger.h"
#include <cassert>
#include <limits>
#include <string>
#include <vector>
using charm::bank::CentLedger;
int main() {
    CentLedger x;
    assert(!x.apply("", 4));
    assert(x.apply("seed", 100) && x.balance() == 100);
    assert(!x.apply("seed", 50) && x.balance() == 100);
    assert(x.apply("exact", -100) && x.balance() == 0);
    assert(!x.apply("over", -1) && x.accepted_ids().size() == 2);
    assert(x.apply("zero", 0));
    CentLedger y;
    assert(y.apply("max", std::numeric_limits<long long>::max()));
    assert(!y.apply("overflow", 1));
    assert((x.accepted_ids() == std::vector<std::string>{"seed", "exact", "zero"}));
    return 0;
}
'''


TRANSFER_REFERENCE = r'''#include <limits>
#include <map>
#include <string>
#include <string_view>
#include <utility>
#include <vector>
namespace charm::bank {
struct Transfer { std::string from; std::string to; long long cents; };
class AccountBook {
public:
    explicit AccountBook(std::map<std::string, long long> balances)
        : balances_(std::move(balances)) {}
    bool execute(const std::vector<Transfer>& plan) {
        std::map<std::string, long long> deltas;
        for (const Transfer& transfer : plan) {
            if (transfer.cents < 0 || balances_.count(transfer.from) == 0U ||
                balances_.count(transfer.to) == 0U) return false;
            if (!add_checked(deltas[transfer.from], -transfer.cents) ||
                !add_checked(deltas[transfer.to], transfer.cents)) return false;
        }
        for (const auto& [name, balance] : balances_) {
            const long long delta = deltas[name];
            if ((delta > 0 && balance > std::numeric_limits<long long>::max() - delta) ||
                (delta < 0 && balance < std::numeric_limits<long long>::min() - delta) ||
                balance + delta < 0) return false;
        }
        for (auto& [name, balance] : balances_) balance += deltas[name];
        return true;
    }
    long long balance_of(std::string_view name) const {
        const auto found = balances_.find(std::string(name));
        return found == balances_.end() ? -1 : found->second;
    }
private:
    static bool add_checked(long long& value, long long delta) {
        if ((delta > 0 && value > std::numeric_limits<long long>::max() - delta) ||
            (delta < 0 && value < std::numeric_limits<long long>::min() - delta)) return false;
        value += delta;
        return true;
    }
    std::map<std::string, long long> balances_;
};
}
'''

TRANSFER_START = r'''#include <map>
#include <string>
#include <string_view>
#include <vector>
namespace charm::bank {
struct Transfer { std::string from; std::string to; long long cents; };
class AccountBook {
public:
    explicit AccountBook(std::map<std::string, long long> balances) : balances_(balances) {}
    bool execute(const std::vector<Transfer>& plan);
    long long balance_of(std::string_view name) const;
private:
    std::map<std::string, long long> balances_;
};
}
'''

TRANSFER_TEST = r'''#include "atomic-transfer-plan.cpp"
#include <cassert>
#include <map>
#include <vector>
using charm::bank::AccountBook;
using charm::bank::Transfer;
int main() {
    AccountBook book({{"a", 10}, {"b", 0}, {"c", 0}});
    assert(book.execute({}) && book.balance_of("a") == 10);
    assert(book.execute({{"a", "b", 7}, {"b", "c", 7}}));
    assert(book.balance_of("a") == 3 && book.balance_of("b") == 0 && book.balance_of("c") == 7);
    assert(!book.execute({{"missing", "a", 1}}));
    assert(!book.execute({{"a", "c", -1}}));
    assert(!book.execute({{"a", "c", 4}}) && book.balance_of("a") == 3);
    assert(book.execute({{"a", "a", 3}}) && book.balance_of("a") == 3);
    assert(book.balance_of("unknown") == -1);
    return 0;
}
'''


CHECKPOINT_REFERENCE = r'''#pragma once
#include <cstddef>
#include <limits>
#include <vector>
namespace charm::bank {
class CheckpointAccount {
public:
    CheckpointAccount(long long initial, long long overdraft_limit, long long fee)
        : balance_(initial), limit_(overdraft_limit < 0 ? 0 : overdraft_limit), fee_(fee < 0 ? 0 : fee) {}
    std::size_t checkpoint() { snapshots_.push_back({balance_, fees_}); return snapshots_.size() - 1; }
    bool withdraw(long long amount) {
        if (amount < 0 || balance_ < std::numeric_limits<long long>::min() + amount) return false;
        long long next = balance_ - amount;
        const bool charge_fee = next < 0;
        if (charge_fee) {
            if (next < std::numeric_limits<long long>::min() + fee_) return false;
            next -= fee_;
        }
        if (next < -limit_) return false;
        balance_ = next;
        if (charge_fee) ++fees_;
        return true;
    }
    void deposit(long long amount) {
        if (amount > 0 && balance_ <= std::numeric_limits<long long>::max() - amount) {
            balance_ += amount;
        }
    }
    bool rollback(std::size_t token) {
        if (token >= snapshots_.size()) return false;
        balance_ = snapshots_[token].balance;
        fees_ = snapshots_[token].fees;
        snapshots_.resize(token + 1);
        return true;
    }
    long long balance() const { return balance_; }
    std::size_t fee_count() const { return fees_; }
private:
    struct Snapshot { long long balance; std::size_t fees; };
    long long balance_;
    long long limit_;
    long long fee_;
    std::size_t fees_ = 0;
    std::vector<Snapshot> snapshots_;
};
}
'''

CHECKPOINT_TEST = r'''#include "checkpointed-overdraft.hpp"
#include <cassert>
using charm::bank::CheckpointAccount;
int main() {
    CheckpointAccount account(20, 15, 2);
    const auto root = account.checkpoint();
    assert(account.withdraw(20) && account.balance() == 0 && account.fee_count() == 0);
    const auto zero = account.checkpoint();
    assert(account.withdraw(5) && account.balance() == -7 && account.fee_count() == 1);
    assert(!account.withdraw(20) && account.balance() == -7 && account.fee_count() == 1);
    assert(account.rollback(zero) && account.balance() == 0 && account.fee_count() == 0);
    account.deposit(4);
    assert(account.rollback(root) && account.balance() == 20);
    assert(!account.rollback(99));
    assert(account.rollback(root));
    CheckpointAccount boundary(0, 5, 2);
    assert(!boundary.withdraw(4) && boundary.balance() == 0 && boundary.fee_count() == 0);
    return 0;
}
'''


def tasks() -> list[dict]:
    ledger_files = ["idempotent-cent-ledger.h", "idempotent-cent-ledger.cpp", "idempotent-cent-ledger_detail.cpp"]
    ledger_prompt = prompt(
        "Idempotent cent ledger",
        "Apply uniquely identified cent transactions exactly once, reject any transition below zero atomically, and preserve accepted-ID order.",
        "namespace charm::bank { class CentLedger { public: bool apply(std::string,long long); long long balance() const; std::vector<std::string> accepted_ids() const; }; }",
        ["empty identifiers are invalid", "duplicate IDs do not apply twice", "an exact withdrawal reaches zero", "overflow and overdraft leave all state unchanged", "a zero delta is accepted once"],
        ledger_files,
    )
    transfer_files = ["atomic-transfer-plan.cpp"]
    transfer_prompt = prompt(
        "Atomic transfer plan",
        "Construct a book from named balances, validate a whole transfer plan, simulate aggregate deltas, and commit only when every final balance is valid.",
        "namespace charm::bank { struct Transfer { std::string from; std::string to; long long cents; }; class AccountBook { public: explicit AccountBook(std::map<std::string,long long>); bool execute(const std::vector<Transfer>&); long long balance_of(std::string_view) const; }; }",
        ["an empty plan succeeds", "unknown accounts reject atomically", "negative amounts reject", "chained funding is based on aggregate final balances", "self-transfer has no net effect"],
        transfer_files,
    )
    checkpoint_files = ["checkpointed-overdraft.hpp"]
    checkpoint_prompt = prompt(
        "Checkpointed overdraft repair",
        "Track balance and overdraft-fee count in checkpoints. Rejected withdrawals change nothing; rollback restores both fields and truncates later checkpoints.",
        "namespace charm::bank { class CheckpointAccount { public: CheckpointAccount(long long,long long,long long); std::size_t checkpoint(); bool withdraw(long long); void deposit(long long); bool rollback(std::size_t); long long balance() const; std::size_t fee_count() const; }; }",
        ["negative deposits are ignored", "exact-balance withdrawal charges no fee", "crossing below zero charges one fee", "invalid rollback is inert", "rollback may be repeated for the retained checkpoint"],
        checkpoint_files,
    )
    return [
        package(topic="Bank Account", task_id="charm-v1-idempotent-cent-ledger", instructions=ledger_prompt,
                editable={ledger_files[0]: LEDGER_START, ledger_files[1]: "#include \"idempotent-cent-ledger.h\"\n", ledger_files[2]: "#include \"idempotent-cent-ledger.h\"\nstatic_assert(false, \"repair anchor\");\n"},
                reference={ledger_files[0]: LEDGER_HEADER, ledger_files[1]: support(ledger_files[0], 11), ledger_files[2]: support(ledger_files[0], 12)},
                hidden_name="idempotent-cent-ledger_test.cpp", hidden=LEDGER_TEST, category="idempotent-transactions", tags=["header-repair", "multi-file", "overflow", "atomicity"]),
        package(topic="Bank Account", task_id="charm-v1-atomic-transfer-plan", instructions=transfer_prompt,
                editable={transfer_files[0]: TRANSFER_START}, reference={transfer_files[0]: TRANSFER_REFERENCE},
                hidden_name="atomic-transfer-plan_test.cpp", hidden=TRANSFER_TEST, category="transaction-simulation", tags=["cpp-include-surface", "atomic-batch", "map", "overflow"]),
        package(topic="Bank Account", task_id="charm-v1-checkpointed-overdraft", instructions=checkpoint_prompt,
                editable={checkpoint_files[0]: "#pragma once\nnamespace charm::bank {}\n"}, reference={checkpoint_files[0]: CHECKPOINT_REFERENCE},
                hidden_name="checkpointed-overdraft_test.cpp", hidden=CHECKPOINT_TEST, category="rollback-state", tags=["header-only", "linker-repair", "snapshots", "state-machine"]),
    ]
