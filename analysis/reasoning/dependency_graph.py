class DependencyGraph:
    
    def __init__(self):
        self.graph = {
            "flask-server": ["proc-python3", "proc-python"],
            "proc-python3": ["proc-python"],
            "proc-python": [],
            "system": [],
        }

    def get_dependencies(self, service):

        return self.graph.get(service, [])

    def get_dependents(self, service):

        dependents = []

        for s, deps in self.graph.items():
            if service in deps:
                dependents.append(s)

        return dependents