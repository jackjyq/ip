// https://stackoverflow.com/questions/2242086/how-to-detect-the-screen-resolution-with-javascript
document.getElementById("width").innerHTML =
  window.screen.width * window.devicePixelRatio;
document.getElementById("height").innerHTML =
  window.screen.height * window.devicePixelRatio;
