import base64
import html
import pathlib
from string import Template


class ColladaHTMLViewer:
    """Helper class to view COLLADA model in html with the help of `three.js`.

    This can display a COLLADA model in IPython compatible environments with the
    implementation of `_repr_html_` method."""

    HTML_TEMPLATE = Template("""
<!DOCTYPE html>
<html>

<head>
    <meta charset="UTF-8" />
    <script type="importmap">
    {
      "imports": {
        "three": "https://unpkg.com/three@0.138.0/build/three.module.js",
        "three-orbitcontrols": "https://unpkg.com/three@0.138.0/examples/jsm/controls/OrbitControls.js",
        "three-collada-loader": "https://unpkg.com/three@0.138.0/examples/jsm/loaders/ColladaLoader.js"
      }
    }
  </script>
</head>

<body>
    <a download="model.dae" id="tqec-3d-viewer-download-link"
        href="data:text/plain;base64,$MODEL_BASE64_PLACEHOLDER">Download 3D Model as .dae File</a>
    <br>Mouse Wheel = Zoom. Left Drag = Orbit. Right Drag = Strafe.
    <div id="tqec-3d-viewer-scene-container" style="width: calc(100vw - 32px); height: calc(100vh - 64px);">JavaScript Blocked?</div>

    <script type="module">
        let container = document.getElementById("tqec-3d-viewer-scene-container");
        let downloadLink = document.getElementById("tqec-3d-viewer-download-link");
        container.textContent = "Loading viewer...";

        /// BEGIN TERRIBLE HACK.
        /// Change the ID to avoid cross-cell interactions.
        /// This is a workaround for https://github.com/jupyter/notebook/issues/6598
        container.id = undefined;
        downloadLink.id = undefined;

        import { Box3, Scene, Color, PerspectiveCamera, WebGLRenderer, AmbientLight, DirectionalLight, Vector3, DoubleSide, AxesHelper } from "three";
        import { OrbitControls } from "three-orbitcontrols";
        import { ColladaLoader } from "three-collada-loader";

        try {
            container.textContent = "Loading model...";
            let modelDataUri = downloadLink.href;
            let collada = await new ColladaLoader().loadAsync(modelDataUri);
            container.textContent = "Loading scene...";

            // Create the scene, adding lighting for the loaded objects.
            let scene = new Scene();
            scene.background = new Color("#CBDFC6");
            // Ambient light
            const ambientLight = new AmbientLight(0xffffff, 3);

            scene.add(ambientLight);

            // Traverse the model to set materials to double-sided
            collada.scene.traverse(function (node) {
                if (node.isMesh) {
                    node.material.side = DoubleSide;
                }
            });
            scene.add(collada.scene);

            // Point the camera at the center, far enough back to see everything.
            let camera = new PerspectiveCamera(35, container.clientWidth / container.clientHeight, 0.1, 100000);
            let controls = new OrbitControls(camera, container);
            let bounds = new Box3().setFromObject(scene);
            let mid = new Vector3(
                (bounds.min.x + bounds.max.x) * 0.5,
                (bounds.min.y + bounds.max.y) * 0.5,
                (bounds.min.z + bounds.max.z) * 0.5,
            );
            let boxPoints = [];
            for (let dx of [0, 0.5, 1]) {
                for (let dy of [0, 0.5, 1]) {
                    for (let dz of [0, 0.5, 1]) {
                        boxPoints.push(new Vector3(
                            bounds.min.x + (bounds.max.x - bounds.min.x) * dx,
                            bounds.min.y + (bounds.max.y - bounds.min.y) * dy,
                            bounds.min.z + (bounds.max.z - bounds.min.z) * dz,
                        ));
                    }
                }
            }
            let isInView = p => {
                p = new Vector3(p.x, p.y, p.z);
                p.project(camera);
                return Math.abs(p.x) < 1 && Math.abs(p.y) < 1 && p.z >= 0 && p.z < 1;
            };
            let unit = new Vector3(0.3, 0.4, -1.8);
            unit.normalize();
            let setCameraDistance = d => {
                controls.target.copy(mid);
                camera.position.copy(mid);
                camera.position.addScaledVector(unit, d);
                controls.update();
                return boxPoints.every(isInView);
            };

            let maxDistance = 1;
            for (let k = 0; k < 20; k++) {
                if (setCameraDistance(maxDistance)) {
                    break;
                }
                maxDistance *= 2;
            }
            let minDistance = maxDistance;
            for (let k = 0; k < 20; k++) {
                minDistance /= 2;
                if (!setCameraDistance(minDistance)) {
                    break;
                }
            }
            for (let k = 0; k < 20; k++) {
                let mid = (minDistance + maxDistance) / 2;
                if (setCameraDistance(mid)) {
                    maxDistance = mid;
                } else {
                    minDistance = mid;
                }
            }
            setCameraDistance(maxDistance);

            // Add axes helper to the scene
            let axesHelper = new AxesHelper(2);
            axesHelper.rotation.x = -Math.PI / 2; // Rotate the axes to align with the model's Z-up orientation
            scene.add(axesHelper);

            // Set up rendering.
            let renderer = new WebGLRenderer({ antialias: true });
            container.textContent = "";
            renderer.setSize(container.clientWidth, container.clientHeight);
            renderer.setPixelRatio(window.devicePixelRatio);
            renderer.physicallyCorrectLights = true;
            container.appendChild(renderer.domElement);

            // Render whenever any important changes have occurred.
            requestAnimationFrame(() => renderer.render(scene, camera));
            new ResizeObserver(() => {
                let w = container.clientWidth;
                let h = container.clientHeight;
                camera.aspect = w / h;
                camera.updateProjectionMatrix();
                renderer.setSize(w, h);
                renderer.render(scene, camera);
            }).observe(container);
            controls.addEventListener("change", () => {
                renderer.render(scene, camera);
            })
        } catch (ex) {
            container.textContent = "Failed to show model. " + ex;
            console.error(ex);
        }
    </script>
</body>
</html>
""")

    def __init__(self, filepath_or_bytes: str | pathlib.Path | bytes) -> None:
        if isinstance(filepath_or_bytes, bytes):
            collada_bytes = filepath_or_bytes
        else:
            with open(filepath_or_bytes, "rb") as file:
                collada_bytes = file.read()
        collada_base64 = base64.b64encode(collada_bytes).decode("utf-8")
        self.html_str = self.HTML_TEMPLATE.substitute(
            MODEL_BASE64_PLACEHOLDER=collada_base64
        )

    def _repr_html_(self) -> str:
        framed = f"""<iframe style="width: 100%; height: 300px; overflow: hidden; resize: both; border: 1px dashed gray;" frameBorder="0" srcdoc="{html.escape(self.html_str, quote=True)}"></iframe>"""
        return framed

    def __str__(self) -> str:
        return self.html_str


def display_collada_model(
    filepath_or_bytes: str | pathlib.Path | bytes,
    write_html_filepath: str | pathlib.Path | None = None,
) -> ColladaHTMLViewer:
    """Display a 3D model from a Collada DAE file in IPython compatible environments.

    This function references the the code snippet from the `stim.Circuit().diagram()` method.

    Args:
        filepath_or_bytes: The input dae file path or bytes of the dae file.
        write_html_filepath: The output html file path to write the generated html content.

    Returns:
        A helper class to display the 3D model, which implements the `_repr_html_` method and
        can be directly displayed in IPython compatible environments.
    """
    helper = ColladaHTMLViewer(filepath_or_bytes)

    if write_html_filepath is not None:
        with open(write_html_filepath, "w") as file:
            file.write(str(helper))

    return helper
