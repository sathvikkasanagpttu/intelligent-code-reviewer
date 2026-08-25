/* Intelligent Code Reviewer — ambient 3D scene
   A slowly-drifting particle/graph network with wireframe "review nodes",
   evoking an always-on system reading and connecting code. Runs behind
   every page at up to 2x pixel density for a crisp, high-resolution feel. */
(function () {
  var canvas = document.getElementById("webgl-bg");
  if (!canvas || typeof THREE === "undefined") return;

  var reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  var renderer;
  try {
    renderer = new THREE.WebGLRenderer({ canvas: canvas, alpha: true, antialias: true, powerPreference: "high-performance" });
  } catch (e) { return; }
  renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
  renderer.setSize(window.innerWidth, window.innerHeight);

  var scene = new THREE.Scene();
  var camera = new THREE.PerspectiveCamera(50, window.innerWidth / window.innerHeight, 0.1, 100);
  camera.position.set(0, 0, 16);

  var group = new THREE.Group();
  scene.add(group);

  // --- node cloud -----------------------------------------------------
  var NODES = 170;
  var pts = [];
  var positions = new Float32Array(NODES * 3);
  for (var i = 0; i < NODES; i++) {
    var v = new THREE.Vector3(
      (Math.random() - 0.5) * 24,
      (Math.random() - 0.5) * 15,
      (Math.random() - 0.5) * 13
    );
    pts.push(v);
    positions[i * 3] = v.x;
    positions[i * 3 + 1] = v.y;
    positions[i * 3 + 2] = v.z;
  }
  var pointsGeo = new THREE.BufferGeometry();
  pointsGeo.setAttribute("position", new THREE.BufferAttribute(positions, 3));
  var pointsMat = new THREE.PointsMaterial({ size: 0.085, color: 0xd7ff4f, transparent: true, opacity: 0.85 });
  group.add(new THREE.Points(pointsGeo, pointsMat));

  // --- graph edges between nearby nodes --------------------------------
  var lineVerts = [];
  var MAX_DIST = 4.4, MAX_LINKS = 3;
  for (var a = 0; a < NODES; a++) {
    var links = 0;
    for (var b = a + 1; b < NODES && links < MAX_LINKS; b++) {
      if (pts[a].distanceTo(pts[b]) < MAX_DIST) {
        lineVerts.push(pts[a].x, pts[a].y, pts[a].z, pts[b].x, pts[b].y, pts[b].z);
        links++;
      }
    }
  }
  var lineGeo = new THREE.BufferGeometry();
  lineGeo.setAttribute("position", new THREE.BufferAttribute(new Float32Array(lineVerts), 3));
  var lineMat = new THREE.LineBasicMaterial({ color: 0x55e6ff, transparent: true, opacity: 0.13 });
  group.add(new THREE.LineSegments(lineGeo, lineMat));

  // --- floating wireframe review-nodes ---------------------------------
  var shapes = [];
  var shapeGeo = new THREE.IcosahedronGeometry(1, 0);
  var palette = [0xd7ff4f, 0x55e6ff, 0xa879ff, 0xffb45e];
  for (var k = 0; k < 5; k++) {
    var mat = new THREE.MeshBasicMaterial({ color: palette[k % palette.length], wireframe: true, transparent: true, opacity: 0.32 });
    var mesh = new THREE.Mesh(shapeGeo, mat);
    var scale = 0.9 + Math.random() * 1.1;
    mesh.scale.setScalar(scale);
    mesh.position.set((Math.random() - 0.5) * 18, (Math.random() - 0.5) * 10, (Math.random() - 0.5) * 6 - 1);
    mesh.userData.speed = 0.12 + Math.random() * 0.22;
    mesh.userData.axis = new THREE.Vector3(Math.random() - 0.5, Math.random() - 0.5, Math.random() - 0.5).normalize();
    group.add(mesh);
    shapes.push(mesh);
  }

  // --- interaction -------------------------------------------------------
  var mouseX = 0, mouseY = 0, curX = 0, curY = 0;
  window.addEventListener("mousemove", function (e) {
    mouseX = e.clientX / window.innerWidth - 0.5;
    mouseY = e.clientY / window.innerHeight - 0.5;
  }, { passive: true });

  window.addEventListener("resize", function () {
    camera.aspect = window.innerWidth / window.innerHeight;
    camera.updateProjectionMatrix();
    renderer.setSize(window.innerWidth, window.innerHeight);
  });

  var clock = new THREE.Clock();
  var running = false;

  function frame() {
    if (!running) return;
    requestAnimationFrame(frame);
    var t = clock.getElapsedTime();
    curX += (mouseX - curX) * 0.02;
    curY += (mouseY - curY) * 0.02;
    group.rotation.y = t * 0.028 + curX * 0.6;
    group.rotation.x = curY * 0.35;
    for (var s = 0; s < shapes.length; s++) {
      shapes[s].rotateOnAxis(shapes[s].userData.axis, shapes[s].userData.speed * 0.01);
    }
    renderer.render(scene, camera);
  }

  function start() {
    if (running) return;
    running = true;
    frame();
  }
  function stop() {
    running = false;
  }

  document.addEventListener("visibilitychange", function () {
    if (document.hidden || reduceMotion) stop(); else start();
  });

  if (reduceMotion) {
    renderer.render(scene, camera); // single static frame — respects reduced motion
  } else {
    start();
  }
})();
