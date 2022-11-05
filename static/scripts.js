// reduce fraction
// https://stackoverflow.com/a/4652513
// Reduce a fraction by finding the Greatest Common Divisor and dividing by it.
function reduceFraction(numerator, denominator) {
  if (isNaN(numerator) || isNaN(denominator)) return NaN;
  var gcd = function gcd(a, b) {
    return b ? gcd(b, a % b) : a;
  };
  gcd = gcd(numerator, denominator);
  return [numerator / gcd, denominator / gcd];
}

// Get the screen detail
// https://stackoverflow.com/questions/2242086/how-to-detect-the-screen-resolution-with-javascript
document.getElementById("resolution").innerHTML =
  window.screen.width + " x " + window.screen.height;
document.getElementById("devicePixelRatio").innerHTML = window.devicePixelRatio;

reducedPair = reduceFraction(window.screen.width, window.screen.height);
document.getElementById("aspectRatio").innerHTML =
  reducedPair[0] + " : " + reducedPair[1];

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
