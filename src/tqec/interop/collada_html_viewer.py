import base64
import html
import pathlib
from string import Template


class ColladaHTMLViewer:
    """Helper class to view COLLADA model in html with the help of `three.js`.

    This can display a COLLADA model in IPython compatible environments with the
    implementation of `_repr_html_` method."""

    HTML_TEMPLATE = Template("""
<!doctype html>
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
  <a download="model.dae" id="model-download-link" href="data:text/plain;base64,$MODEL_BASE64_PLACEHOLDER">Download 3D
    Model as .dae File</a>
  <br />Mouse Wheel = Zoom. Left Drag = Orbit. Right Drag = Strafe.
  <div id="scene-container" style="width: calc(100vw - 32px); height: calc(100vh - 64px)">
    JavaScript Blocked?
  </div>

  <script type="module">
    import * as THREE from "three";
    import {OrbitControls} from "three-orbitcontrols";
    import {ColladaLoader} from "three-collada-loader";

    const container = document.getElementById("scene-container");
    const downloadLink = document.getElementById("model-download-link");

    // Remove IDs to avoid cross-cell interactions (workaround for Jupyter notebook issue)
    container.removeAttribute("id");
    downloadLink.removeAttribute("id");

    container.textContent = "Loading viewer...";

    async function init() {
      try {
        container.textContent = "Loading model...";

        const modelDataUri = downloadLink.href;
        const collada = await new ColladaLoader().loadAsync(modelDataUri);

        container.textContent = "Loading scene...";

        // Create the scene
        const scene = new THREE.Scene();
        scene.background = new THREE.Color("#CBDFC6");

        // Set up lights
        setupLights(scene);

        // Prepare and add the model to the scene
        processModel(collada.scene);
        scene.add(collada.scene);

        // Set up the camera and controls
        const camera = new THREE.PerspectiveCamera(
          35,
          container.clientWidth / container.clientHeight,
          0.1,
          100000,
        );
        const controls = new OrbitControls(camera, container);

        // Adjust camera to fit the scene
        fitCameraToObject(camera, controls, scene);

        // Add axes helper
        const axesHelper = new THREE.AxesHelper(2);
        axesHelper.rotation.x = -Math.PI / 2;
        scene.add(axesHelper);

        // Set up renderer
        const renderer = new THREE.WebGLRenderer({antialias: true});
        setupRenderer(renderer, container, camera, scene);

        // Start rendering
        renderScene(renderer, scene, camera, controls, container);
      } catch (ex) {
        container.textContent = "Failed to show model. " + ex;
        console.error(ex);
      }
    }

    function setupLights(scene) {
      const ambientLight = new THREE.AmbientLight(0xffffff, 1.4);
      scene.add(ambientLight);

      const directionalLight = new THREE.DirectionalLight(0xffffff, 1.0);
      directionalLight.position.set(10, 10, 10);
      directionalLight.castShadow = true;
      scene.add(directionalLight);
    }

    function processModel(modelScene) {
      modelScene.traverse((node) => {
        if (node.isMesh) {
          node.material.side = THREE.DoubleSide;

          if (node.name.endsWith("correlation_surface")) {
            return;
          }
          // Add edges for better visibility
          const edgesGeometry = new THREE.EdgesGeometry(node.geometry);
          const edgesMaterial = new THREE.LineBasicMaterial({
            color: 0x000000,
          });
          const edgeMesh = new THREE.LineSegments(
            edgesGeometry,
            edgesMaterial,
          );
          node.add(edgeMesh);
        }
      });
    }

    function fitCameraToObject(camera, controls, scene) {
      const bounds = new THREE.Box3().setFromObject(scene);
      const center = bounds.getCenter(new THREE.Vector3());
      const size = bounds.getSize(new THREE.Vector3());

      // Compute the distance required to fit the object
      const maxDim = Math.max(size.x, size.y, size.z);
      const fov = camera.fov * (Math.PI / 180);
      let cameraZ = Math.abs(maxDim / 2 / Math.tan(fov / 2));

      camera.position.set(center.x, center.y, cameraZ * 1.2);
      camera.lookAt(center);

      // Update the controls target and update the controls
      controls.target.copy(center);
      controls.update();
    }

    function setupRenderer(renderer, container, camera, scene) {
      container.textContent = "";
      renderer.setSize(container.clientWidth, container.clientHeight);
      renderer.setPixelRatio(window.devicePixelRatio);
      renderer.physicallyCorrectLights = true;
      renderer.toneMapping = THREE.ACESFilmicToneMapping;
      renderer.toneMappingExposure = 1.2;
      renderer.outputEncoding = THREE.sRGBEncoding;
      renderer.setClearColor(0xdedede);
      container.appendChild(renderer.domElement);
    }

    function renderScene(renderer, scene, camera, controls, container) {
      const render = () => {
        renderer.render(scene, camera);
      };

      render();

      new ResizeObserver(() => {
        const width = container.clientWidth;
        const height = container.clientHeight;
        camera.aspect = width / height;
        camera.updateProjectionMatrix();
        renderer.setSize(width, height);
        render();
      }).observe(container);

      controls.addEventListener("change", render);
    }

    init();
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
