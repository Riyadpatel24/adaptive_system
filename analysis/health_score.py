def calculate_health(metrics):

    cpu = metrics["cpu"]
    memory = metrics["memory"]
    disk = metrics["disk"]

    health = 100 - (
        cpu * 0.3 +
        memory * 0.4 +
        disk * 0.3
    )

    if health > 80:
        status = "STABLE"

    elif health > 50:
        status = "WARNING"

    else:
        status = "CRITICAL"

    return health, status