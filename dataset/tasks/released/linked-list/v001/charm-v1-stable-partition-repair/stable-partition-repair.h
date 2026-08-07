#pragma once
#include <memory>
#include <vector>
namespace charm::list {
class StableList {
public:
    void push_back(int value) {
        auto node = std::make_unique<Node>(value);
        Node* raw = node.get();
        if (!head_) head_ = std::move(node); else tail_->next = std::move(node);
        tail_ = raw;
    }
    void partition(int threshold) {
        std::unique_ptr<Node> low_head, high_head;
        Node* low_tail = nullptr;
        Node* high_tail = nullptr;
        while (head_) {
            auto node = std::move(head_);
            head_ = std::move(node->next);
            Node*& destination_tail = node->value >= threshold ? low_tail : high_tail;
            std::unique_ptr<Node>& destination_head = node->value >= threshold ? low_head : high_head;
            Node* raw = node.get();
            if (!destination_head) destination_head = std::move(node); else destination_tail->next = std::move(node);
            destination_tail = raw;
        }
        if (low_head) { head_ = std::move(low_head); low_tail->next = std::move(high_head); tail_ = high_tail ? high_tail : low_tail; }
        else { head_ = std::move(high_head); tail_ = high_tail; }
    }
    std::vector<int> values() const {
        std::vector<int> out;
        for (Node* node = head_.get(); node; node = node->next.get()) out.push_back(node->value);
        return out;
    }
private:
    struct Node { explicit Node(int input) : value(input) {} int value; std::unique_ptr<Node> next; };
    std::unique_ptr<Node> head_;
    Node* tail_ = nullptr;
};
}
