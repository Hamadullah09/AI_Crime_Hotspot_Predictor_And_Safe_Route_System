import heapq
from collections import deque


AREA_COORDINATES = {
    "clifton": (1, 1),
    "dha": (2, 1),
    "defence-view": (2, 5),
    "saddar": (2, 4),
    "garden": (2, 3),
    "kharadar": (1, 4),
    "lyari": (1, 5),
    "keamari": (1, 6),
    "baldia-town": (0, 3),
    "orangi-town": (1, 2),
    "banaras": (2, 2),
    "site-area": (2, 3),
    "nazimabad": (3, 4),
    "north-nazimabad": (4, 3),
    "sakhi-hasan": (4, 2),
    "fb-area": (5, 2),
    "new-karachi": (5, 1),
    "surjani-town": (6, 0),
    "sohrab-goth": (7, 1),
    "gulberg": (4, 3),
    "gulshan": (5, 3),
    "jamshed-town": (5, 4),
    "pechs": (5, 5),
    "mehmoodabad": (5, 6),
    "gulistan-e-johar": (7, 4),
    "scheme-33": (8, 2),
    "shah-faisal": (8, 5),
    "malir": (9, 4),
    "korangi": (8, 6),
    "landhi": (9, 6),
}


def _heuristic(current_area, destination_area):
    current_x, current_y = AREA_COORDINATES.get(current_area, (0, 0))
    destination_x, destination_y = AREA_COORDINATES.get(destination_area, (0, 0))
    return abs(current_x - destination_x) + abs(current_y - destination_y)


def _travel_cost(neighbor_area, area_risk_scores, time_of_day):
    area_score = area_risk_scores.get(neighbor_area, 1)
    night_penalty = 1.5 if time_of_day == "night" else 0
    return 1 + area_score + night_penalty


def build_safe_route(start_area, destination_area, area_connections, area_risk_scores, time_of_day):
    """
    A beginner-friendly A* route search.
    Higher-risk areas cost more, so safer paths are preferred.
    """
    if start_area == destination_area:
        return [start_area]

    open_nodes = []
    heapq.heappush(open_nodes, (0, start_area))

    came_from = {}
    g_score = {start_area: 0}

    while open_nodes:
        _, current_area = heapq.heappop(open_nodes)

        if current_area == destination_area:
            return _reconstruct_path(came_from, current_area)

        for neighbor in area_connections.get(current_area, []):
            tentative_g_score = g_score[current_area] + _travel_cost(
                neighbor_area=neighbor,
                area_risk_scores=area_risk_scores,
                time_of_day=time_of_day,
            )

            if tentative_g_score < g_score.get(neighbor, float("inf")):
                came_from[neighbor] = current_area
                g_score[neighbor] = tentative_g_score
                f_score = tentative_g_score + _heuristic(neighbor, destination_area)
                heapq.heappush(open_nodes, (f_score, neighbor))

    return [start_area, destination_area]


def build_direct_route(start_area, destination_area, area_connections):
    """Return the shortest unweighted route for comparison with the safer route."""
    if start_area == destination_area:
        return [start_area]

    queue = deque([[start_area]])
    visited = {start_area}

    while queue:
        path = queue.popleft()
        current_area = path[-1]

        for neighbor in area_connections.get(current_area, []):
            if neighbor in visited:
                continue

            next_path = path + [neighbor]
            if neighbor == destination_area:
                return next_path

            visited.add(neighbor)
            queue.append(next_path)

    return [start_area, destination_area]


def _reconstruct_path(came_from, current_area):
    path = [current_area]
    while current_area in came_from:
        current_area = came_from[current_area]
        path.append(current_area)
    path.reverse()
    return path
