// get resolution
document.getElementById("resolution").innerHTML =
  window.screen.width * window.devicePixelRatio +
  " x " +
  window.screen.height * window.devicePixelRatio;

// get color depth
document.getElementById("colorDepth").innerHTML =
  window.screen.colorDepth + " 位";

// Get device location
const latitude_element = document.getElementById("latitude");
const longitude_element = document.getElementById("longitude");
const address_element = document.getElementById("address");
navigator.geolocation.getCurrentPosition(
  (position) => {
    const latitude = position.coords.latitude;
    const longitude = position.coords.longitude;
    latitude_element.innerHTML = latitude;
    longitude_element.innerHTML = longitude;
    fetch(
      "/address?" +
        new URLSearchParams({ latitude: latitude, longitude: longitude }),
      {
        method: "GET",
      }
    )
      .then((response) => {
        return response.json();
      })
      .then((data) => {
        address_element.innerHTML = data.address;
      });
  },
  (error) => {
    latitude_element.innerHTML = "获取失败";
    longitude_element.innerHTML = "获取失败";
    address_element.innerHTML = "未知";
  }
);

// get gpu
var canvas = document.createElement("canvas");
var gl;
var debugInfo;
var vendor;
var renderer;

try {
  gl = canvas.getContext("webgl") || canvas.getContext("experimental-webgl");
} catch (e) {}

if (gl) {
  debugInfo = gl.getExtension("WEBGL_debug_renderer_info");
  vendor = gl.getParameter(debugInfo.UNMASKED_VENDOR_WEBGL);
  renderer = gl.getParameter(debugInfo.UNMASKED_RENDERER_WEBGL);
}

document.getElementById("gpu").innerHTML = renderer;
