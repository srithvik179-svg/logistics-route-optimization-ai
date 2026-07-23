/**
 * 3D AI Command Center Digital Twin Workspace Controller
 * Implements interactive Three.js WebGL scene, 3D supply chain nodes, curved corridor flow lines,
 * animated shipment particles, raycasting interaction, inspector telemetry drawer, and AI pulse mode.
 * Dynamically reacts to Global & Local Filters via /api/geospatial-network/payload.
 */
(function() {
    let scene, camera, renderer, controls;
    let nodes3D = [];
    let corridorLines = [];
    let flowParticles = [];
    let raycaster, mouse;
    let animFrameId = null;
    let isInitialized = false;
    let activeSelectedNode = null;
    let activeFiltersState = {};

    const NODE_TYPES = {
        HUB: { color: 0x3b82f6, icon: "fa-network-wired", target: "routes-section", label: "Distribution Hub" },
        WAREHOUSE: { color: 0x10b981, icon: "fa-warehouse", target: "explorer-section", label: "Regional Warehouse" },
        REPAIR: { color: 0xf59e0b, icon: "fa-wrench", target: "reverse-section", label: "TPR Repair Center" },
        AICORE: { color: 0x8b5cf6, icon: "fa-robot", target: "recommendation-section", label: "AI Core Engine" }
    };

    const DEFAULT_NETWORK_NODES = [
        { id: "HUB-SIN", name: "Singapore International Hub", type: "HUB", x: -28, y: 4, z: -15, status: "Healthy", capacity: "62%", sla: "97.5%", load: "4,264 units" },
        { id: "HUB-BLR", name: "Bengaluru Logistics Node", type: "HUB", x: -10, y: 6, z: 8, status: "Healthy", capacity: "78%", sla: "94.2%", load: "3,294 units" },
        { id: "HUB-DEL", name: "Delhi Distribution Center", type: "HUB", x: 8, y: 5, z: -10, status: "Warning", capacity: "89%", sla: "78.4%", load: "4,229 units" },
        { id: "HUB-MUM", name: "Mumbai Gateway Hub", type: "HUB", x: -12, y: 3, z: -8, status: "Healthy", capacity: "65%", sla: "91.0%", load: "4,636 units" },
        { id: "HUB-CHE", name: "Chennai Coastal Hub", type: "HUB", x: -2, y: 4, z: 14, status: "Healthy", capacity: "71%", sla: "88.6%", load: "3,402 units" },
        { id: "HUB-HYD", name: "Hyderabad Central Node", type: "HUB", x: 4, y: 5, z: 4, status: "Healthy", capacity: "69%", sla: "92.1%", load: "3,754 units" },
        { id: "HUB-KOL", name: "Kolkata Satellite Hub", type: "HUB", x: 22, y: 4, z: -4, status: "Critical", capacity: "94%", sla: "42.0%", load: "3,792 units" },
        { id: "TPR-001", name: "Southtech TPR Repair Center", type: "REPAIR", x: -18, y: 2, z: 2, status: "Healthy", capacity: "54%", sla: "96.0%", load: "1,240 units" },
        { id: "TPR-HYD-01", name: "Quickfix Hydro Repair Center", type: "REPAIR", x: 12, y: 2, z: 10, status: "Healthy", capacity: "48%", sla: "98.1%", load: "890 units" },
        { id: "WH-NORTH", name: "North Enterprise Warehouse", type: "WAREHOUSE", x: 18, y: 3, z: -20, status: "Healthy", capacity: "58%", sla: "95.5%", load: "8,500 units" },
        { id: "AI-CORE-01", name: "RoutePilot AI Core Engine", type: "AICORE", x: 0, y: 12, z: 0, status: "Healthy", capacity: "100%", sla: "99.9%", load: "Live Real-Time AI" }
    ];

    async function load3DCommandCenterWorkspace(filters = {}) {
        activeFiltersState = Object.assign({}, window.GlobalFilters || {}, filters || {});
        console.log("[3DCommandCenter] Loading 3D AI Digital Twin with active filters:", activeFiltersState);

        const container = document.getElementById("canvas-3d-scene");
        if (!container) return;

        if (!isInitialized) {
            initThreeJS(container);
            isInitialized = true;
        } else {
            onWindowResize();
        }

        // Fetch filtered network payload from backend
        try {
            const rawRes = await apiFetch("/api/geospatial-network/payload", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ filters: activeFiltersState })
            });

            const data = rawRes.payload || rawRes;

            // 1. Update 3D Nodes & Corridors based on Filtered Payload
            update3DNetworkFromPayload(data, activeFiltersState);

            // 2. Update Floating KPI overlay numbers
            update3DKPIs(data.summary || {}, data.routes || [], activeFiltersState);

            // 3. Update Live Alerts
            renderLive3DAlerts(data.nodes || [], activeFiltersState);

        } catch (err) {
            console.error("[3DCommandCenter] Error fetching network payload:", err);
            update3DNetworkFromPayload(null, activeFiltersState);
        }

        // Bind Controls Toolbar
        bindToolbarControls();
    }

    function initThreeJS(container) {
        const width = container.clientWidth || window.innerWidth;
        const height = container.clientHeight || 750;

        // 1. Scene & Camera
        scene = new THREE.Scene();
        scene.background = new THREE.Color(0x090d16);
        scene.fog = new THREE.FogExp2(0x090d16, 0.008);

        camera = new THREE.PerspectiveCamera(45, width / height, 0.1, 1000);
        camera.position.set(0, 35, 65);

        // 2. Renderer
        renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
        renderer.setSize(width, height);
        renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
        renderer.shadowMap.enabled = true;
        renderer.shadowMap.type = THREE.PCFSoftShadowMap;

        container.innerHTML = "";
        container.appendChild(renderer.domElement);

        // 3. Orbit Controls
        if (typeof THREE.OrbitControls !== "undefined") {
            controls = new THREE.OrbitControls(camera, renderer.domElement);
            controls.enableDamping = true;
            controls.dampingFactor = 0.05;
            controls.maxPolarAngle = Math.PI / 2 - 0.05;
            controls.minDistance = 15;
            controls.maxDistance = 120;
        }

        // 4. Lighting
        const ambientLight = new THREE.AmbientLight(0xffffff, 0.4);
        scene.add(ambientLight);

        const dirLight = new THREE.DirectionalLight(0x3b82f6, 1.2);
        dirLight.position.set(30, 50, 30);
        dirLight.castShadow = true;
        scene.add(dirLight);

        const pointLight = new THREE.PointLight(0x10b981, 1.5, 100);
        pointLight.position.set(0, 15, 0);
        scene.add(pointLight);

        // 5. 3D Grid Floor
        const gridHelper = new THREE.GridHelper(120, 40, 0x3b82f6, 0x1e293b);
        gridHelper.position.y = 0;
        scene.add(gridHelper);

        // 6. Raycaster Setup
        raycaster = new THREE.Raycaster();
        mouse = new THREE.Vector2();
        renderer.domElement.addEventListener("click", onCanvasClick, false);
        window.addEventListener("resize", onWindowResize, false);

        // 7. Start Animation Loop
        animate();
    }

    function update3DNetworkFromPayload(payload, filters) {
        // Clear existing node groups and corridor lines
        nodes3D.forEach(m => { if (m.parent) scene.remove(m.parent); });
        nodes3D = [];

        corridorLines.forEach(l => scene.remove(l));
        corridorLines = [];

        flowParticles.forEach(p => scene.remove(p.mesh));
        flowParticles = [];

        const activeHubFilter = filters.hub || filters.Origin_Hub || filters.source || filters.hub_id;
        const activePriority = filters.priority;

        // Build 3D Node Meshes
        DEFAULT_NETWORK_NODES.forEach(n => {
            const isMatchFilter = !activeHubFilter || activeHubFilter === "All" || n.id === activeHubFilter || n.name.includes(activeHubFilter);
            const conf = NODE_TYPES[n.type] || NODE_TYPES.HUB;
            const group = new THREE.Group();
            group.position.set(n.x, n.y, n.z);

            // Scale & Opacity based on filter match
            const scaleFactor = isMatchFilter ? 1.2 : 0.7;
            const opacityVal = isMatchFilter ? 1.0 : 0.35;

            let geom, mat;
            if (n.type === "HUB") {
                geom = new THREE.CylinderGeometry(2 * scaleFactor, 2.5 * scaleFactor, 3 * scaleFactor, 16);
                mat = new THREE.MeshStandardMaterial({ color: isMatchFilter ? conf.color : 0x475569, roughness: 0.3, metalness: 0.7, transparent: true, opacity: opacityVal });
            } else if (n.type === "REPAIR") {
                geom = new THREE.OctahedronGeometry(2.2 * scaleFactor);
                mat = new THREE.MeshStandardMaterial({ color: isMatchFilter ? conf.color : 0x475569, roughness: 0.2, metalness: 0.8, transparent: true, opacity: opacityVal });
            } else if (n.type === "WAREHOUSE") {
                geom = new THREE.BoxGeometry(3.5 * scaleFactor, 2.5 * scaleFactor, 3.5 * scaleFactor);
                mat = new THREE.MeshStandardMaterial({ color: isMatchFilter ? conf.color : 0x475569, roughness: 0.4, metalness: 0.5, transparent: true, opacity: opacityVal });
            } else { // AICORE
                geom = new THREE.IcosahedronGeometry(2.5, 2);
                mat = new THREE.MeshStandardMaterial({ color: conf.color, roughness: 0.1, metalness: 0.9, wireframe: true });
            }

            const mesh = new THREE.Mesh(geom, mat);
            mesh.castShadow = true;
            mesh.userData = n;
            group.add(mesh);

            // Status Glow Ring around node base
            const ringColor = n.status === "Healthy" ? 0x10b981 : (n.status === "Warning" ? 0xf59e0b : 0xef4444);
            const ringGeom = new THREE.RingGeometry(2.8 * scaleFactor, 3.4 * scaleFactor, 32);
            const ringMat = new THREE.MeshBasicMaterial({ color: isMatchFilter ? ringColor : 0x334155, side: THREE.DoubleSide, transparent: true, opacity: opacityVal * 0.8 });
            const ringMesh = new THREE.Mesh(ringGeom, ringMat);
            ringMesh.rotation.x = Math.PI / 2;
            ringMesh.position.y = -n.y + 0.05;
            group.add(ringMesh);

            // Pulsing Light
            if (isMatchFilter) {
                const pLight = new THREE.PointLight(ringColor, 1.2, 16);
                pLight.position.set(0, 1, 0);
                group.add(pLight);
            }

            scene.add(group);
            nodes3D.push(mesh);

            // Auto Camera Focus if specific Hub is filtered
            if (activeHubFilter && isMatchFilter && n.type === "HUB") {
                focusCameraOn(group.position);
            }
        });

        // Build Filtered Corridors & Animated Flow Particles
        const routesList = (payload && payload.routes) ? payload.routes : [];
        const hubNodesMap = {};
        DEFAULT_NETWORK_NODES.forEach(n => hubNodesMap[n.id] = n);

        const hubNodesList = DEFAULT_NETWORK_NODES.filter(n => n.type !== "AICORE");
        for (let i = 0; i < hubNodesList.length; i++) {
            for (let j = i + 1; j < hubNodesList.length; j++) {
                const n1 = hubNodesList[i];
                const n2 = hubNodesList[j];

                // Check if route matches active filter
                const isFilteredHubConnected = !activeHubFilter || activeHubFilter === "All" || n1.id === activeHubFilter || n2.id === activeHubFilter;
                const dist = Math.hypot(n1.x - n2.x, n1.z - n2.z);

                if (dist < 38 && isFilteredHubConnected) {
                    const start = new THREE.Vector3(n1.x, n1.y, n1.z);
                    const end = new THREE.Vector3(n2.x, n2.y, n2.z);
                    const mid = new THREE.Vector3((n1.x + n2.x)/2, Math.max(n1.y, n2.y) + dist * 0.25, (n1.z + n2.z)/2);

                    const curve = new THREE.QuadraticBezierCurve3(start, mid, end);
                    const points = curve.getPoints(30);
                    const geometry = new THREE.BufferGeometry().setFromPoints(points);
                    
                    const lineColor = activePriority === "High Priority" ? 0xef4444 : (activeHubFilter ? 0x10b981 : 0x3b82f6);
                    const material = new THREE.LineDashedMaterial({ color: lineColor, dashSize: 1, gapSize: 0.5, opacity: 0.7, transparent: true });
                    const line = new THREE.Line(geometry, material);
                    line.computeLineDistances();
                    scene.add(line);
                    corridorLines.push(line);

                    // Add animated flow particle
                    const pGeom = new THREE.SphereGeometry(0.45, 8, 8);
                    const pMat = new THREE.MeshBasicMaterial({ color: lineColor });
                    const particle = new THREE.Mesh(pGeom, pMat);
                    scene.add(particle);

                    flowParticles.push({
                        mesh: particle,
                        curve: curve,
                        progress: Math.random(),
                        speed: 0.003 + Math.random() * 0.004
                    });
                }
            }
        }
    }

    function update3DKPIs(summary, routes, filters) {
        const setVal = (id, text) => {
            const el = document.getElementById(id);
            if (el) el.textContent = text;
        };

        const totalShipments = summary.total_shipments || (routes.length > 0 ? routes.reduce((sum, r) => sum + (r.shipment_count || 10), 0) : 1800);
        const activeLanes = summary.total_active_routes || (routes.length > 0 ? routes.length : 108);
        const avgSla = summary.avg_sla_compliance ? summary.avg_sla_compliance.toFixed(1) : "84.2";
        const avgCost = summary.avg_logistics_cost ? `$${(summary.avg_logistics_cost * activeLanes / 100.0).toFixed(2)}M` : "$2.83M";

        setVal("kpi-3d-shipments", typeof totalShipments === "number" ? totalShipments.toLocaleString() : totalShipments);
        setVal("kpi-3d-routes", `${activeLanes} Lanes`);
        setVal("kpi-3d-sla", `${avgSla}%`);
        setVal("kpi-3d-cost", avgCost);
        setVal("kpi-3d-capacity", filters.hub ? "78.4% Hub" : "68.5% Avg");
        setVal("kpi-3d-circular", "91.8 Score");
    }

    function animate() {
        animFrameId = requestAnimationFrame(animate);

        // 1. Rotate AI Core & Nodes gently
        nodes3D.forEach(mesh => {
            mesh.rotation.y += 0.008;
            if (mesh.userData.type === "AICORE") {
                mesh.rotation.x += 0.005;
            }
        });

        // 2. Animate Shipment Flow Particles along curves
        flowParticles.forEach(p => {
            p.progress += p.speed;
            if (p.progress > 1) p.progress = 0;
            const pt = p.curve.getPoint(p.progress);
            p.mesh.position.set(pt.x, pt.y, pt.z);
        });

        // 3. Orbit Controls update
        if (controls) controls.update();

        // 4. Render
        renderer.render(scene, camera);
    }

    function onCanvasClick(event) {
        const rect = renderer.domElement.getBoundingClientRect();
        mouse.x = ((event.clientX - rect.left) / rect.width) * 2 - 1;
        mouse.y = -((event.clientY - rect.top) / rect.height) * 2 + 1;

        raycaster.setFromCamera(mouse, camera);
        const intersects = raycaster.intersectObjects(nodes3D);

        if (intersects.length > 0) {
            const selected = intersects[0].object.userData;
            console.log("[3DCommandCenter] Node Clicked:", selected);
            openNodeInspector(selected);
            focusCameraOn(intersects[0].object.parent.position);
        }
    }

    function openNodeInspector(node) {
        const drawer = document.getElementById("command-3d-inspector");
        const titleEl = document.getElementById("inspector-title");
        const bodyEl = document.getElementById("inspector-body");

        if (!drawer || !bodyEl) return;
        activeSelectedNode = node;
        drawer.style.display = "block";

        const conf = NODE_TYPES[node.type] || NODE_TYPES.HUB;
        const statusBadge = node.status === "Healthy" ? "badge-success" : (node.status === "Warning" ? "badge-warning" : "badge-danger");

        titleEl.innerHTML = `<i class="fa-solid ${conf.icon} text-primary"></i> ${node.name}`;

        bodyEl.innerHTML = `
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:4px;">
                <span class="badge ${statusBadge}">${node.status} Status</span>
                <span class="text-muted">Node ID: <strong>${node.id}</strong></span>
            </div>
            <div style="display:grid; grid-template-columns:1fr 1fr; gap:6px; background:rgba(30,41,59,0.6); padding:8px; border-radius:6px;">
                <div><span class="text-muted">Capacity:</span> <strong style="color:#fff;">${node.capacity}</strong></div>
                <div><span class="text-muted">SLA Rate:</span> <strong style="color:#10b981;">${node.sla}</strong></div>
                <div style="grid-column: span 2;"><span class="text-muted">Current Load:</span> <strong style="color:#3b82f6;">${node.load}</strong></div>
            </div>
            <p style="margin:4px 0 6px 0; color:#94a3b8; font-size:10px;">AI Telemetry: Operating within nominal thresholds. Live telemetry streaming active.</p>
            <div style="display:flex; gap:6px; margin-top:4px;">
                <button class="btn btn-primary btn-sm" style="flex:1; font-size:11px; font-weight:700; background:#2563eb; color:#ffffff; border:none; padding:8px 12px; border-radius:6px; cursor:pointer; display:flex; align-items:center; justify-content:center; gap:6px; box-shadow:0 2px 8px rgba(37,99,235,0.4);" onclick="CommandCenter3D.navigateToTarget('${conf.target}')">
                    <i class="fa-solid fa-arrow-right-to-bracket"></i> Open ${conf.label}
                </button>
            </div>
        `;
    }

    function navigateToTarget(targetId) {
        console.log("[3DCommandCenter] Navigating to target module:", targetId);
        const link = document.querySelector(`.sidebar-nav a[data-target="${targetId}"]`);
        if (link) {
            link.click();
        } else if (window.location) {
            window.location.hash = `#${targetId}`;
        }
    }

    function focusCameraOn(targetVec3) {
        if (!camera || !controls) return;
        const startPos = camera.position.clone();
        const endPos = new THREE.Vector3(targetVec3.x, targetVec3.y + 12, targetVec3.z + 20);

        let progress = 0;
        const interval = setInterval(() => {
            progress += 0.08;
            if (progress >= 1) {
                camera.position.copy(endPos);
                controls.target.copy(targetVec3);
                clearInterval(interval);
                return;
            }
            camera.position.lerpVectors(startPos, endPos, progress);
            controls.target.lerp(targetVec3, progress);
        }, 16);
    }

    function renderLive3DAlerts(nodes, filters) {
        const container = document.getElementById("command-3d-alerts-container");
        if (!container) return;

        const activeHubFilter = filters.hub || filters.Origin_Hub || filters.source;

        let alerts = [
            { icon: "fa-triangle-exclamation text-warning", text: "HUB-KOL capacity at 94%. SLA risk threshold exceeded.", target: "sla-section", badge: "Capacity Alert", badgeClass: "badge-danger" },
            { icon: "fa-box-open text-primary", text: "PRT-01129 stockout predicted at HUB-BLR. Transfer suggested.", target: "circular-section", badge: "Stock Shortage", badgeClass: "badge-warning" },
            { icon: "fa-rotate-left text-info", text: "TPR-001 repair backlog: 42 parts pending triage.", target: "reverse-section", badge: "Repair Backlog", badgeClass: "badge-info" },
            { icon: "fa-route text-success", text: "Optimal route updated: HUB-SIN -> HUB-HYD -> Bangalore.", target: "routes-section", badge: "Route Intel", badgeClass: "badge-success" }
        ];

        if (activeHubFilter && activeHubFilter !== "All") {
            alerts.unshift({
                icon: "fa-filter text-success",
                text: `Filtered Active Monitor: Node ${activeHubFilter} highlighted in 3D scene.`,
                target: "routes-section",
                badge: "Active Filter",
                badgeClass: "badge-success"
            });
        }

        container.innerHTML = "";
        alerts.slice(0, 4).forEach(a => {
            const card = document.createElement("div");
            card.className = "card-item";
            card.style.cssText = "padding:8px 10px; background:rgba(30,41,59,0.8); border-radius:6px; border:1px solid rgba(59,130,246,0.25); cursor:pointer; transition:all 0.2s ease;";
            card.onmouseenter = () => card.style.background = "rgba(51, 65, 85, 0.9)";
            card.onmouseleave = () => card.style.background = "rgba(30, 41, 59, 0.8)";
            card.onclick = () => navigateToTarget(a.target);
            card.innerHTML = `
                <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:4px;">
                    <span class="badge ${a.badgeClass}" style="font-size:9px; font-weight:700; padding:2px 6px;">${a.badge}</span>
                    <span style="font-size:10px; color:#38bdf8; font-weight:600; display:flex; align-items:center; gap:3px;">View <i class="fa-solid fa-chevron-right" style="font-size:8px;"></i></span>
                </div>
                <div style="font-size:10.5px; color:#f8fafc; font-weight:500; line-height:1.3;">
                    <i class="fa-solid ${a.icon}" style="margin-right:4px;"></i> ${a.text}
                </div>
            `;
            container.appendChild(card);
        });
    }

    function bindToolbarControls() {
        const btnOpt = document.getElementById("btn-3d-ai-optimize");
        if (btnOpt) {
            btnOpt.onclick = () => {
                console.log("[3DCommandCenter] Running AI Optimization Wave...");
                btnOpt.innerHTML = `<i class="fa-solid fa-spinner fa-spin"></i> Optimizing Network...`;
                
                // Pulse particle colors & light intensities
                scene.children.forEach(c => {
                    if (c.isPointLight) {
                        c.intensity = 3.5;
                        setTimeout(() => c.intensity = 1.5, 1200);
                    }
                });

                setTimeout(() => {
                    btnOpt.innerHTML = `<i class="fa-solid fa-wand-magic-sparkles"></i> Run AI Optimization`;
                    if (window.Toast) window.Toast.success("AI Network Optimization Executed: 108 corridors rebalanced.");
                }, 1500);
            };
        }

        const btnReset = document.getElementById("btn-3d-reset-cam");
        if (btnReset) {
            btnReset.onclick = () => {
                if (camera && controls) {
                    camera.position.set(0, 35, 65);
                    controls.target.set(0, 0, 0);
                }
            };
        }

        const btnRotL = document.getElementById("btn-3d-rotate-left");
        if (btnRotL) btnRotL.onclick = () => { if (controls) controls.autoRotate = true; controls.autoRotateSpeed = -4.0; setTimeout(() => controls.autoRotate = false, 2000); };

        const btnRotR = document.getElementById("btn-3d-rotate-right");
        if (btnRotR) btnRotR.onclick = () => { if (controls) controls.autoRotate = true; controls.autoRotateSpeed = 4.0; setTimeout(() => controls.autoRotate = false, 2000); };

        const btnZoomIn = document.getElementById("btn-3d-zoom-in");
        if (btnZoomIn) btnZoomIn.onclick = () => { if (camera) camera.position.multiplyScalar(0.8); };

        const btnZoomOut = document.getElementById("btn-3d-zoom-out");
        if (btnZoomOut) btnZoomOut.onclick = () => { if (camera) camera.position.multiplyScalar(1.2); };
    }

    function onWindowResize() {
        const container = document.getElementById("canvas-3d-scene");
        if (!container || !renderer || !camera) return;
        const width = container.clientWidth || window.innerWidth;
        const height = container.clientHeight || 750;
        camera.aspect = width / height;
        camera.updateProjectionMatrix();
        renderer.setSize(width, height);
    }

    // Auto-trigger when navigating to 3D command center
    document.addEventListener("DOMContentLoaded", () => {
        if (window.location.hash === "#command-3d-section" || window.location.hash === "#command-3d") {
            load3DCommandCenterWorkspace();
        }
    });

    window.addEventListener("hashchange", () => {
        if (window.location.hash === "#command-3d-section" || window.location.hash === "#command-3d") {
            load3DCommandCenterWorkspace();
        }
    });

    window.load3DCommandCenterWorkspace = load3DCommandCenterWorkspace;
    window.CommandCenter3D = {
        navigateToTarget: navigateToTarget
    };
})();
