class SqlVisitor:
    def visit(self, node1, node2):
        visitor = getattr(self, f"visit_{node1.__class__.__name__}_{node2.__class__.__name__}", self.generic_visit)
        return visitor(node1, node2)

    def generic_visit(self, node1, node2):
        raise NotImplementedError(f"No visit_{node1.__class__.__name__}_{node2.__class__.__name__} method")