class DependencyGraph:

    def __init__(self):

        self.graph = {
            "api_service": ["auth_service", "database"],
            "auth_service": ["database"],
            "database": ["disk"],
            "cache": ["memory"]
        }

    def get_dependencies(self, service):

        return self.graph.get(service, [])

    def get_dependents(self, service):

        dependents = []

        for s, deps in self.graph.items():
            if service in deps:
                dependents.append(s)

        return dependents