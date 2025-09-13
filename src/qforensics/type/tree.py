from __future__ import annotations


class Node:
    def __init__(self, parent: Node):
        self.parent = parent
        self.children: list[Node] = []

    def row(self):
        if self.parent:
            return self.parent.children.index(self)
        return 0
