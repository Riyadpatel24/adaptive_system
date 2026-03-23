class RootCauseEngine:

    def __init__(self, dependency_graph):
        self.graph = dependency_graph

    def find_root_cause(self, entity_health):

        failing_services = [
            service for service, data in entity_health.items()
            if data["state"] == "CRITICAL"
        ]

        if not failing_services:
            return None

        for service in failing_services:

            deps = self.graph.get_dependencies(service)

            for dep in deps:

                if dep in entity_health and entity_health[dep]["state"] == "critical":
                    return dep

        return failing_services[0]