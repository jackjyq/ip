// get memory
document.getElementById("memory").innerHTML =
  window.navigator.deviceMemory === undefined
    ? "未知"
    : window.navigator.deviceMemory + " GB";

// get CPU
document.getElementById("cpu").innerHTML =
  window.navigator.hardwareConcurrency === undefined
    ? "未知"
    : window.navigator.hardwareConcurrency + " 核";

// get user language
document.getElementById("user_language").innerHTML =
  window.navigator.languages.toString();

// get user timezone
document.getElementById("user_timezone").innerHTML =
  Intl.DateTimeFormat().resolvedOptions().timeZone;

// get user_time
document.getElementById("user_time").innerHTML = new Date().toLocaleString(
  "zh-CN"
);

//  get fps
// Refs: https://stackoverflow.com/questions/6131051/is-it-possible-to-find-out-what-is-the-monitor-frame-rate-in-javascript
const getFPS = () =>
  new Promise((resolve) =>
    requestAnimationFrame((t1) =>
      requestAnimationFrame((t2) => resolve(1000 / (t2 - t1)))
    )
  );

getFPS().then((fps) => (document.getElementById("fps").innerHTML = fps));

// get touch screen
document.getElementById("touchscreen").innerHTML =
  navigator.maxTouchPoints > 1 ? "有" : "无";

// get input devices
// Refs: fpCollect.min.js
function getInputDevices() {
  return new Promise((resolve) => {
    const deviceToCount = {
      audiooutput: 0,
      audioinput: 0,
      videoinput: 0,
    };

    if (
      navigator.mediaDevices &&
      navigator.mediaDevices.enumerateDevices &&
      navigator.mediaDevices.enumerateDevices.name !== "bound reportBlock"
    ) {
      // bound reportBlock occurs with Brave
      navigator.mediaDevices.enumerateDevices().then((devices) => {
        if (typeof devices !== "undefined") {
          let name;
          for (let i = 0; i < devices.length; i++) {
            name = [devices[i].kind];
            deviceToCount[name] = deviceToCount[name] + 1;
          }
          resolve({
            speakers: deviceToCount.audiooutput,
            micros: deviceToCount.audioinput,
            webcams: deviceToCount.videoinput,
          });
        } else {
          resolve({
            speakers: 0,
            micros: 0,
            webcams: 0,
          });
        }
      });
    } else if (
      navigator.mediaDevices &&
      navigator.mediaDevices.enumerateDevices &&
      navigator.mediaDevices.enumerateDevices.name === "bound reportBlock"
    ) {
      resolve({
        devicesBlockedByBrave: true,
      });
    } else {
      resolve({
        speakers: 0,
        micros: 0,
        webcams: 0,
      });
    }
  });
}

getInputDevices().then((value) => {
  document.getElementById("speakers").innerHTML =
    value.speakers > 0 ? "有" : "无";
  document.getElementById("webcams").innerHTML =
    value.webcams > 0 ? "有" : "无";
  document.getElementById("micros").innerHTML = value.micros > 0 ? "有" : "无";
});

// get anti bot information
document.getElementById("webdriver").innerHTML = navigator.webdriver;
document.getElementById("chrome").innerHTML = window.chrome ? "是" : "否";
document.getElementById("plugins").innerHTML = navigator.plugins.length;
