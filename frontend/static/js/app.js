const form = document.getElementById("route-form");
const startSelect = document.getElementById("start");
const destinationSelect = document.getElementById("destination");
const timeSelect = document.getElementById("time");
const submitButton = document.getElementById("submit-button");
const statusMessage = document.getElementById("status-message");
const coverageCountElement = document.getElementById("coverage-count");
const incidentCountElement = document.getElementById("incident-count");
const journeySummaryElement = document.getElementById("journey-summary");
const riskBadgeElement = document.getElementById("risk-badge");
const riskScoreElement = document.getElementById("risk-score");
const riskLevelElement = document.getElementById("risk-level");
const alertTextElement = document.getElementById("alert-text");
const riskGaugeFillElement = document.getElementById("risk-gauge-fill");
const hotspotListElement = document.getElementById("hotspot-list");
const heatmapBandsElement = document.getElementById("heatmap-bands");
const safeRouteElement = document.getElementById("safe-route");
const recommendationsElement = document.getElementById("recommendations");
const routeRationaleElement = document.getElementById("route-rationale");
const supportedAreasElement = document.getElementById("supported-areas");
const bayesianScoreElement = document.getElementById("bayesian-score");
const knnScoreElement = document.getElementById("knn-score");
const decisionTreeScoreElement = document.getElementById("decision-tree-score");
const decisionTreeDetailElement = document.getElementById("decision-tree-detail");
const combinedScoreElement = document.getElementById("combined-score");
const safeRouteStepsElement = document.getElementById("safe-route-steps");
const directRouteStepsElement = document.getElementById("direct-route-steps");
const safeRouteRiskTextElement = document.getElementById("safe-route-risk-text");
const directRouteRiskTextElement = document.getElementById("direct-route-risk-text");
const routeIncidentTotalElement = document.getElementById("route-incident-total");
const routeDayNightTextElement = document.getElementById("route-day-night-text");
const routeCrimeFocusElement = document.getElementById("route-crime-focus");
const routeCrimeTextElement = document.getElementById("route-crime-text");
const routeCoveredAreasElement = document.getElementById("route-covered-areas");
const mapSvgElement = document.getElementById("map-svg");
const mapPanelElement = document.getElementById("map-panel");
const toggleMapSizeButton = document.getElementById("toggle-map-size");

const MAP_VIEWBOX = { width: 100, height: 100 };
const MAP_SAFE_BOUNDS = { left: 6, right: 94, top: 8, bottom: 92 };
const CARD_BOUNDS = { left: 2, right: 98, top: 3, bottom: 97 };

let networkOverviewCache = { areas: [], hotspot_zones: [], selected_time: "day" };
let activeRouteKeys = [];

async function bootstrapDashboard() {
    let areasLoaded = false;

    try {
        const supportedAreasResponse = await fetch("/api/supported-areas");
        const supportedAreasData = await supportedAreasResponse.json();
        populateAreaOptions(supportedAreasData.supported_areas || []);
        areasLoaded = true;
    } catch (_error) {
        statusMessage.textContent = "Unable to load start and destination areas.";
    }

    await refreshOverview(timeSelect.value || "day", areasLoaded);
}

async function refreshOverview(timeValue, areasLoaded = true) {
    try {
        const response = await fetch(`/api/network-overview?time=${encodeURIComponent(timeValue || "day")}`);
        const overview = await response.json();
        networkOverviewCache = overview;
        renderSupportedAreas(overview.areas || []);
        renderHotspots(overview.hotspot_zones || []);
        renderHeatmapBands(overview.heatmap_bands || []);
        renderMap(overview.areas || [], activeRouteKeys);
        coverageCountElement.textContent = `${(overview.areas || []).length} zones`;
        incidentCountElement.textContent = `${overview.network_summary?.total_incidents || 0} incidents`;
        statusMessage.textContent = areasLoaded
            ? "Threat network synchronized."
            : "Map loaded, but area list had an issue.";
    } catch (_error) {
        coverageCountElement.textContent = areasLoaded ? "Map unavailable" : "Unavailable";
        statusMessage.textContent = areasLoaded
            ? "Area list loaded, but map overview failed."
            : "Unable to load network overview.";
        hotspotListElement.innerHTML = "<li class='placeholder-item'>Hotspot feed unavailable.</li>";
    }
}

function populateAreaOptions(areaNames) {
    const cleanedNames = [...new Set(areaNames)].sort((left, right) => left.localeCompare(right));
    const optionMarkup = cleanedNames
        .map((areaName) => `<option value="${escapeText(areaName)}">${escapeText(areaName)}</option>`)
        .join("");

    startSelect.innerHTML = '<option value="">Select start location</option>';
    destinationSelect.innerHTML = '<option value="">Select destination</option>';
    startSelect.insertAdjacentHTML("beforeend", optionMarkup);
    destinationSelect.insertAdjacentHTML("beforeend", optionMarkup);
}

function renderSupportedAreas(areas) {
    supportedAreasElement.innerHTML = areas
        .map((area) => `<span class="area-pill">${escapeText(area.name)}</span>`)
        .join("");
}

function renderHotspots(hotspots) {
    hotspotListElement.innerHTML = hotspots
        .map(
            (zone) => `
                <li class="hotspot-item">
                    <div>
                        <strong>${escapeText(zone.name)}</strong>
                        <small>${escapeText(zone.risk_level)} risk surveillance zone</small>
                    </div>
                    <span class="hotspot-score">${formatScore(zone.risk_score)}</span>
                </li>
            `
        )
        .join("");
}

function renderHeatmapBands(bands) {
    heatmapBandsElement.innerHTML = bands
        .map(
            (band) => `
                <div class="heat-band">
                    <div>
                        <strong>${escapeText(band.name)}</strong>
                        <small>${escapeText(band.top_crime_type || band.risk_level)} focus</small>
                    </div>
                    <div class="heat-track">
                        <div class="heat-fill" style="width: ${Math.max(band.intensity * 100, 10)}%"></div>
                    </div>
                    <span class="heat-value">${band.incident_total || 0}</span>
                </div>
            `
        )
        .join("");
}

function renderRouteUrbanSummary(routeUrbanSummary) {
    const coveredAreas = routeUrbanSummary?.covered_areas || [];
    const topCrimes = routeUrbanSummary?.top_route_crimes || [];

    routeIncidentTotalElement.textContent = String(routeUrbanSummary?.total_incidents ?? 0);
    routeDayNightTextElement.textContent = `Day incidents: ${routeUrbanSummary?.day_incidents ?? 0} | Night incidents: ${routeUrbanSummary?.night_incidents ?? 0}`;
    routeCrimeFocusElement.textContent = topCrimes.length ? topCrimes[0].name : "-";
    routeCrimeTextElement.textContent = topCrimes.length
        ? topCrimes.map((crime) => `${crime.name} (${crime.count})`).join(" | ")
        : "No route crime mix available.";

    routeCoveredAreasElement.innerHTML = coveredAreas.length
        ? coveredAreas
            .map(
                (area) => `<span class="area-pill">${escapeText(area.name)} | ${area.incident_total} incidents | ${escapeText(area.top_crime_type)}</span>`
            )
            .join("")
        : "<span class=\"area-pill\">Route-covered urban areas will appear here.</span>";
}

function renderMap(areas, activeRoute) {
    if (!Array.isArray(areas) || !areas.length) {
        mapSvgElement.innerHTML = "";
        return;
    }

    const areaMap = Object.fromEntries(areas.map((area) => [area.key, area]));
    const routeSet = new Set(activeRoute);
    const displayPositions = buildDisplayPositions(areas, activeRoute);
    const labelLayouts = buildLabelLayouts(areas, displayPositions, activeRoute);
    const routePoints = activeRoute
        .map((key) => {
            const point = displayPositions[key];
            const area = areaMap[key];
            if (!point || !area) {
                return null;
            }
            return { ...point, key, name: area.name };
        })
        .filter(Boolean);
    const routeMarkup = buildRouteMarkup(routePoints);

    mapSvgElement.setAttribute("viewBox", `0 0 ${MAP_VIEWBOX.width} ${MAP_VIEWBOX.height}`);
    mapSvgElement.innerHTML = `
        <defs>
            <linearGradient id="route-gradient" x1="0%" y1="0%" x2="100%" y2="0%">
                <stop offset="0%" stop-color="#4dd28a"></stop>
                <stop offset="58%" stop-color="#f4b942"></stop>
                <stop offset="100%" stop-color="#fa7b36"></stop>
            </linearGradient>
            <filter id="route-glow" x="-40%" y="-40%" width="180%" height="180%">
                <feGaussianBlur stdDeviation="1.6" result="blur"></feGaussianBlur>
                <feMerge>
                    <feMergeNode in="blur"></feMergeNode>
                    <feMergeNode in="SourceGraphic"></feMergeNode>
                </feMerge>
            </filter>
            <filter id="card-shadow" x="-30%" y="-30%" width="160%" height="160%">
                <feDropShadow dx="0" dy="1.1" stdDeviation="1.4" flood-color="rgba(0,0,0,0.35)"></feDropShadow>
            </filter>
            <clipPath id="map-board-clip">
                <rect x="1.5" y="1.5" width="97" height="97" rx="5.6"></rect>
            </clipPath>
        </defs>
        <g clip-path="url(#map-board-clip)">
            ${buildConnectionMarkup(areas, displayPositions, routeSet)}
            ${routeMarkup.lineMarkup}
            ${buildNodeMarkup(areas, displayPositions, labelLayouts, activeRoute, areaMap)}
            ${routeMarkup.markerMarkup}
        </g>
    `;
}

function buildDisplayPositions(areas, activeRoute) {
    const routeSet = new Set(activeRoute);
    const points = areas.map((area) => ({
        key: area.key,
        rawX: Number(area.x) || 0,
        rawY: Number(area.y) || 0,
    }));

    const allXs = points.map((point) => point.rawX);
    const allYs = points.map((point) => point.rawY);
    const routePoints = points.filter((point) => routeSet.has(point.key));
    const focusPoints = routePoints.length >= 2 ? routePoints : points;

    const allBounds = getBounds(points);
    const focusBounds = getBounds(focusPoints);
    const expandedFocusBounds = {
        minX: focusBounds.minX - 0.25,
        maxX: focusBounds.maxX + 0.25,
        minY: focusBounds.minY - 0.25,
        maxY: focusBounds.maxY + 0.25,
    };

    const baseBounds = {
        minX: Math.min(allBounds.minX, expandedFocusBounds.minX),
        maxX: Math.max(allBounds.maxX, expandedFocusBounds.maxX),
        minY: Math.min(allBounds.minY, expandedFocusBounds.minY),
        maxY: Math.max(allBounds.maxY, expandedFocusBounds.maxY),
    };

    const spanX = Math.max(baseBounds.maxX - baseBounds.minX, 0.1);
    const spanY = Math.max(baseBounds.maxY - baseBounds.minY, 0.1);
    const paddedBounds = {
        minX: baseBounds.minX - Math.max(spanX * 0.1, 0.25),
        maxX: baseBounds.maxX + Math.max(spanX * 0.1, 0.25),
        minY: baseBounds.minY - Math.max(spanY * 0.12, 0.25),
        maxY: baseBounds.maxY + Math.max(spanY * 0.12, 0.25),
    };

    return Object.fromEntries(
        points.map((point) => [
            point.key,
            {
                x: normalizePoint(point.rawX, paddedBounds.minX, paddedBounds.maxX, MAP_SAFE_BOUNDS.left, MAP_SAFE_BOUNDS.right),
                y: normalizePoint(point.rawY, paddedBounds.minY, paddedBounds.maxY, MAP_SAFE_BOUNDS.top, MAP_SAFE_BOUNDS.bottom),
            },
        ])
    );
}

function buildConnectionMarkup(areas, displayPositions, routeSet) {
    const seen = new Set();
    const fragments = [];

    areas.forEach((area) => {
        (area.connections || []).forEach((target) => {
            const edgeKey = [area.key, target].sort().join("|");
            if (seen.has(edgeKey) || !displayPositions[target]) {
                return;
            }
            seen.add(edgeKey);

            const start = displayPositions[area.key];
            const end = displayPositions[target];
            const highlighted = routeSet.has(area.key) || routeSet.has(target);

            fragments.push(
                `<line class="map-edge${highlighted ? " route-nearby" : ""}" x1="${start.x}" y1="${start.y}" x2="${end.x}" y2="${end.y}"></line>`
            );
        });
    });

    return `<g class="map-edges">${fragments.join("")}</g>`;
}

function buildRouteMarkup(routePoints) {
    if (routePoints.length === 0) {
        return { lineMarkup: "", markerMarkup: "" };
    }

    if (routePoints.length === 1) {
        const point = routePoints[0];
        return {
            lineMarkup: "",
            markerMarkup: `
                <g class="route-markers">
                    <circle class="route-trace-point start-point" cx="${point.x}" cy="${point.y}" r="1.5"></circle>
                </g>
            `,
        };
    }

    const routePath = buildOrthogonalRoutePath(routePoints);
    return {
        lineMarkup: `
            <g class="route-layer" filter="url(#route-glow)">
                <path class="route-trace-glow" d="${routePath}"></path>
                <path class="route-trace-line" d="${routePath}"></path>
            </g>
        `,
        markerMarkup: `
            <g class="route-markers">
                ${buildRouteMarkers(routePoints)}
            </g>
        `,
    };
}

function buildOrthogonalRoutePath(points) {
    if (points.length === 2) {
        return `M ${points[0].x.toFixed(2)} ${points[0].y.toFixed(2)} L ${points[1].x.toFixed(2)} ${points[1].y.toFixed(2)}`;
    }

    const commands = [`M ${points[0].x.toFixed(2)} ${points[0].y.toFixed(2)}`];

    for (let index = 0; index < points.length - 1; index += 1) {
        const current = points[index];
        const next = points[index + 1];
        const previous = points[index - 1] || current;
        const following = points[index + 2] || next;

        const outgoingControl = getCurveControlPoint(previous, current, next, 0.18);
        const incomingControl = getCurveControlPoint(current, next, following, -0.18);

        commands.push(
            `C ${outgoingControl.x.toFixed(2)} ${outgoingControl.y.toFixed(2)} ${incomingControl.x.toFixed(2)} ${incomingControl.y.toFixed(2)} ${next.x.toFixed(2)} ${next.y.toFixed(2)}`
        );
    }

    return commands.join(" ");
}

function getCurveControlPoint(previous, current, next, factor) {
    return {
        x: current.x + ((next.x - previous.x) * factor),
        y: current.y + ((next.y - previous.y) * factor),
    };
}

function buildRouteMarkers(routePoints) {
    return routePoints
        .map((point, index) => {
            const classes = [
                "route-trace-point",
                index === 0 ? "start-point" : "",
                index === routePoints.length - 1 ? "end-point" : "",
            ].filter(Boolean).join(" ");
            const radius = index === 0 || index === routePoints.length - 1 ? 1.85 : 1.15;
            const labelWidth = Math.min(Math.max((point.name.length * 0.62) + 3.8, 7.8), 18);
            const direction = index % 2 === 0 ? -1 : 1;
            const labelHeight = 3.4;
            const proposedTop = point.y + (direction < 0 ? -(labelHeight + 3.1) : 1.8);
            const labelTop = clampPoint(proposedTop, CARD_BOUNDS.top + 0.8, CARD_BOUNDS.bottom - labelHeight - 0.8);
            const labelLeft = clampPoint(point.x - (labelWidth / 2), CARD_BOUNDS.left + 0.6, CARD_BOUNDS.right - labelWidth - 0.6);
            const labelClass = [
                "route-step-label",
                index === 0 ? "start-label" : "",
                index === routePoints.length - 1 ? "end-label" : "",
            ].filter(Boolean).join(" ");

            return `
                <g class="route-step-group">
                    <line class="route-step-link" x1="${point.x}" y1="${point.y}" x2="${(labelLeft + (labelWidth / 2)).toFixed(2)}" y2="${(labelTop + (labelHeight / 2)).toFixed(2)}"></line>
                    <rect class="${labelClass}" x="${labelLeft.toFixed(2)}" y="${labelTop.toFixed(2)}" width="${labelWidth.toFixed(2)}" height="${labelHeight}" rx="1.55"></rect>
                    <text class="route-step-text" x="${(labelLeft + (labelWidth / 2)).toFixed(2)}" y="${(labelTop + 2.18).toFixed(2)}">${escapeText(point.name)}</text>
                    <circle class="${classes}" cx="${point.x}" cy="${point.y}" r="${radius}"></circle>
                </g>
            `;
        })
        .join("");
}

function buildNodeMarkup(areas, displayPositions, labelLayouts, activeRoute) {
    const routeSet = new Set(activeRoute);
    const startKey = activeRoute[0];
    const endKey = activeRoute[activeRoute.length - 1];

    return `
        <g class="map-label-links">
            ${areas.map((area) => buildLinkMarkup(area, displayPositions[area.key], labelLayouts[area.key])).join("")}
        </g>
        <g class="map-nodes">
            ${areas.map((area) => buildSingleNodeMarkup(area, displayPositions[area.key], labelLayouts[area.key], routeSet, startKey, endKey)).join("")}
        </g>
    `;
}

function buildLinkMarkup(area, position, layout) {
    const anchorX = layout.left + (layout.width / 2);
    const anchorY = layout.top + (layout.height / 2);
    return `<line class="map-node-link" x1="${position.x}" y1="${position.y}" x2="${anchorX}" y2="${anchorY}"></line>`;
}

function buildSingleNodeMarkup(area, position, layout, routeSet, startKey, endKey) {
    const riskClass = `${area.risk_level.toLowerCase()}-risk`;
    const cardClasses = [
        "map-node-card",
        routeSet.has(area.key) ? "route-node" : "",
        area.key === startKey ? "start-node" : "",
        area.key === endKey ? "end-node" : "",
    ].filter(Boolean).join(" ");

    const pinRadius = area.key === startKey || area.key === endKey ? 1.55 : 1.05;
    const pingRadius = pinRadius + 0.85;

    return `
        <g class="map-node-group ${routeSet.has(area.key) ? "route-node-group" : ""}">
            <circle class="map-node-ping ${riskClass}" cx="${position.x}" cy="${position.y}" r="${pingRadius}"></circle>
            <circle class="map-node-pin ${riskClass}" cx="${position.x}" cy="${position.y}" r="${pinRadius}"></circle>
            <g filter="url(#card-shadow)">
                <rect class="${cardClasses}" x="${layout.left}" y="${layout.top}" width="${layout.width}" height="${layout.height}" rx="2.4"></rect>
            </g>
            <text class="map-node-title" x="${layout.left + 1.45}" y="${layout.top + 1.25}">
                ${escapeText(area.name)}
            </text>
            <text class="map-node-risk ${riskClass}" x="${layout.left + 1.45}" y="${layout.top + layout.height - 1.05}">
                ${escapeText(area.risk_level)}
            </text>
        </g>
    `;
}

function buildLabelLayouts(areas, displayPositions, activeRoute) {
    const routeSet = new Set(activeRoute);
    const orderedAreas = [...areas].sort((left, right) => {
        const leftPriority = getLayoutPriority(left, routeSet, activeRoute);
        const rightPriority = getLayoutPriority(right, routeSet, activeRoute);
        return rightPriority - leftPriority;
    });

    const placements = {};
    const occupied = [];

    orderedAreas.forEach((area) => {
        const position = displayPositions[area.key];
        const cardSize = getCardSize(area.name, routeSet.has(area.key));
        const candidates = buildLabelCandidates(position, cardSize, routeSet.has(area.key), area.key === activeRoute[0], area.key === activeRoute[activeRoute.length - 1]);

        let bestCandidate = null;
        let bestScore = Number.POSITIVE_INFINITY;

        candidates.forEach((candidate, index) => {
            const rect = clampRectToBounds(candidate, cardSize);
            const overlapPenalty = occupied.reduce((sum, existing) => sum + getRectOverlap(rect, existing), 0);
            const routeBias = routeSet.has(area.key) ? 0 : index * 0.2;
            const centerPenalty = Math.abs((rect.left + (rect.width / 2)) - position.x) * 0.04;
            const score = overlapPenalty + routeBias + centerPenalty + index * 0.06;

            if (score < bestScore) {
                bestScore = score;
                bestCandidate = rect;
            }
        });

        placements[area.key] = bestCandidate;
        occupied.push(bestCandidate);
    });

    return placements;
}

function getLayoutPriority(area, routeSet, activeRoute) {
    let priority = Number(area.risk_score || 0);
    if (routeSet.has(area.key)) {
        priority += 12;
    }
    if (area.key === activeRoute[0] || area.key === activeRoute[activeRoute.length - 1]) {
        priority += 8;
    }
    return priority;
}

function buildLabelCandidates(position, size, isRouteNode, isStartNode, isEndNode) {
    const baseGap = isRouteNode ? 2.4 : 2;
    const verticalLift = isStartNode || isEndNode ? 4.2 : 3;

    return [
        { left: position.x + baseGap, top: position.y - size.height - 0.9 },
        { left: position.x - size.width - baseGap, top: position.y - size.height - 0.9 },
        { left: position.x + baseGap, top: position.y + 1.4 },
        { left: position.x - size.width - baseGap, top: position.y + 1.4 },
        { left: position.x - (size.width / 2), top: position.y - size.height - verticalLift },
        { left: position.x - (size.width / 2), top: position.y + 2.1 },
        { left: position.x - size.width - 3.2, top: position.y - (size.height / 2) },
        { left: position.x + 3.2, top: position.y - (size.height / 2) },
    ];
}

function clampRectToBounds(candidate, size) {
    return {
        left: clampPoint(candidate.left, CARD_BOUNDS.left, CARD_BOUNDS.right - size.width),
        top: clampPoint(candidate.top, CARD_BOUNDS.top, CARD_BOUNDS.bottom - size.height),
        width: size.width,
        height: size.height,
    };
}

function getCardSize(name, isRouteNode) {
    const baseWidth = 7.8 + (Math.min(name.length, 22) * 0.34);
    return {
        width: isRouteNode ? Math.min(baseWidth + 0.8, 17.6) : Math.min(baseWidth, 16.6),
        height: isRouteNode ? 6.2 : 5.6,
    };
}

function getRectOverlap(left, right) {
    const overlapX = Math.max(0, Math.min(left.left + left.width, right.left + right.width) - Math.max(left.left, right.left));
    const overlapY = Math.max(0, Math.min(left.top + left.height, right.top + right.height) - Math.max(left.top, right.top));
    return overlapX * overlapY;
}

function getBounds(points) {
    return {
        minX: Math.min(...points.map((point) => point.rawX)),
        maxX: Math.max(...points.map((point) => point.rawX)),
        minY: Math.min(...points.map((point) => point.rawY)),
        maxY: Math.max(...points.map((point) => point.rawY)),
    };
}

function normalizePoint(value, minRaw, maxRaw, minOut, maxOut) {
    const ratio = (value - minRaw) / Math.max(maxRaw - minRaw, 0.001);
    return minOut + (clampPoint(ratio, 0, 1) * (maxOut - minOut));
}

function clampPoint(value, min, max) {
    return Math.min(Math.max(value, min), max);
}

function renderRoute(routeSequence) {
    safeRouteElement.innerHTML = routeSequence
        .map(
            (step, index) => `
                <li class="route-stop">
                    <span class="stop-index">${index + 1}</span>
                    <div>
                        <span class="route-role">${getRouteRoleLabel(step.role)}</span>
                        <strong>${escapeText(step.name)}</strong>
                        <p>${getStopDescription(index, routeSequence.length, step.role)}</p>
                    </div>
                </li>
            `
        )
        .join("");
}

function getRouteRoleLabel(role) {
    if (role === "start") {
        return "Start";
    }
    if (role === "destination") {
        return "Destination";
    }
    return "Route Step";
}

function getStopDescription(index, totalStops, role) {
    if (role === "start" || index === 0) {
        return "Departure zone selected for route monitoring.";
    }
    if (role === "destination" || index === totalStops - 1) {
        return "Destination reached through the current safest route.";
    }
    return "Intermediate reroute point added to reduce hotspot exposure.";
}

function renderRecommendations(recommendations) {
    recommendationsElement.innerHTML = recommendations
        .map((item) => `<li>${escapeText(item)}</li>`)
        .join("");
}

function renderRouteRationale(reasons) {
    routeRationaleElement.innerHTML = reasons
        .map((item) => `<li>${escapeText(item)}</li>`)
        .join("");
}

function updateRiskBadge(riskLevel) {
    const normalizedRisk = riskLevel.toLowerCase();
    riskBadgeElement.classList.remove("risk-low", "risk-medium", "risk-high", "risk-neutral");
    riskLevelElement.classList.remove("risk-low", "risk-medium", "risk-high");

    if (["low", "medium", "high"].includes(normalizedRisk)) {
        riskBadgeElement.classList.add(`risk-${normalizedRisk}`);
        riskLevelElement.classList.add(`risk-${normalizedRisk}`);
        riskBadgeElement.textContent = `${riskLevel} Risk`;
    } else {
        riskBadgeElement.classList.add("risk-neutral");
        riskBadgeElement.textContent = "Awaiting Input";
    }
}

function updateGauge(score) {
    const cappedScore = Math.min(Math.max(Number(score) || 0, 0), 5);
    const angle = (cappedScore / 5) * 360;
    let gaugeColor = "var(--accent)";

    if (cappedScore >= 3.5) {
        gaugeColor = "var(--high)";
    } else if (cappedScore >= 2) {
        gaugeColor = "var(--medium)";
    } else if (cappedScore > 0) {
        gaugeColor = "var(--low)";
    }

    riskGaugeFillElement.style.background = `conic-gradient(from -90deg, ${gaugeColor} ${angle}deg, rgba(120, 187, 198, 0.08) ${angle}deg)`;
}

function applyAnalysis(data) {
    const routeSequence = Array.isArray(data.route_sequence) && data.route_sequence.length
        ? data.route_sequence
        : (data.safe_route || []).map((name, index, route) => ({
            key: null,
            name,
            role: index === 0 ? "start" : index === route.length - 1 ? "destination" : "step",
        }));
    activeRouteKeys = routeSequence
        .map((step) => step.key)
        .filter(Boolean);

    riskScoreElement.textContent = formatScore(data.risk_score);
    riskLevelElement.textContent = data.risk_level;
    alertTextElement.textContent = data.alert;
    bayesianScoreElement.textContent = formatScore(data.algorithm_breakdown?.bayesian_score);
    knnScoreElement.textContent = formatScore(data.algorithm_breakdown?.knn_score);
    decisionTreeScoreElement.textContent = formatScore(data.algorithm_breakdown?.decision_tree_score);
    decisionTreeDetailElement.textContent = buildDecisionTreeDetail(data.algorithm_breakdown || {});
    combinedScoreElement.textContent = formatScore(data.algorithm_breakdown?.combined_score);
    journeySummaryElement.textContent = `${data.start} to ${data.destination} during ${data.time} travel shows ${data.risk_level.toLowerCase()} exposure with a ${routeSequence.length}-step safer movement plan.`;

    updateRiskBadge(data.risk_level);
    updateGauge(data.risk_score);
    renderRoute(routeSequence);
    renderRecommendations(data.recommendations || []);
    renderRouteRationale(data.route_rationale || []);
    renderRouteUrbanSummary(data.route_urban_summary || {});
    renderHotspots(data.network_overview?.hotspot_zones || []);
    renderHeatmapBands(data.network_overview?.heatmap_bands || []);
    renderMap(data.network_overview?.areas || networkOverviewCache.areas || [], activeRouteKeys);
    safeRouteStepsElement.textContent = data.route_comparison?.safe_route_steps ?? "-";
    directRouteStepsElement.textContent = data.route_comparison?.direct_route_steps ?? "-";
    safeRouteRiskTextElement.textContent = `Exposure score: ${formatScore(data.route_comparison?.safe_route_risk)}`;
    directRouteRiskTextElement.textContent = `Exposure score: ${formatScore(data.route_comparison?.direct_route_risk)} | Reduction: ${formatScore(data.route_comparison?.risk_reduction)}`;
}

function buildDecisionTreeDetail(algorithmBreakdown) {
    if (!algorithmBreakdown.decision_tree_model_available) {
        return "Decision Tree dependency unavailable; fallback area score is being shown.";
    }

    const confidence = algorithmBreakdown.decision_tree_confidence === null || algorithmBreakdown.decision_tree_confidence === undefined
        ? "-"
        : `${Math.round(Number(algorithmBreakdown.decision_tree_confidence) * 100)}%`;
    const trainingRecords = algorithmBreakdown.decision_tree_training_records ?? "-";
    return `${algorithmBreakdown.decision_tree_level || "Unknown"} risk prediction | ${confidence} confidence | ${trainingRecords} training rows.`;
}

function formatScore(score) {
    if (score === undefined || score === null || Number.isNaN(Number(score))) {
        return "-";
    }
    return Number(score).toFixed(2);
}

function escapeText(value) {
    return String(value ?? "")
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#39;");
}

form.addEventListener("submit", async (event) => {
    event.preventDefault();
    statusMessage.textContent = "Analyzing live route threat picture...";
    submitButton.disabled = true;

    const payload = {
        start: startSelect.value,
        destination: destinationSelect.value,
        time: timeSelect.value,
    };

    try {
        const response = await fetch("/api/predict-route", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload),
        });

        const data = await response.json();
        if (!response.ok) {
            throw new Error(data.error || "Route analysis failed.");
        }

        networkOverviewCache = data.network_overview || networkOverviewCache;
        applyAnalysis(data);
        statusMessage.textContent = "Route analysis complete.";
    } catch (error) {
        statusMessage.textContent = error.message;
        journeySummaryElement.textContent = "Unable to generate route intelligence for the current input.";
    } finally {
        submitButton.disabled = false;
    }
});

timeSelect.addEventListener("change", async () => {
    activeRouteKeys = [];
    updateRiskBadge("Awaiting");
    await refreshOverview(timeSelect.value || "day");
});

toggleMapSizeButton.addEventListener("click", () => {
    const expanded = mapPanelElement.classList.toggle("map-panel--expanded");
    document.body.classList.toggle("map-expanded", expanded);
    toggleMapSizeButton.textContent = expanded ? "Close Large Map" : "View Larger Map";
    renderMap(networkOverviewCache.areas || [], activeRouteKeys);
});

bootstrapDashboard();
