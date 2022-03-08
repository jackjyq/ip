const ip = document.getElementById("ip");

function query() {
  let params = new URLSearchParams();
  params.set("ip", ip.textContent);
  window.location.search = params.toString();
}

ip.addEventListener("blur", query);
// bind query() to pressing enter
ip.addEventListener("keyup", (event) => {
  if (event.code == "Enter") {
    query();
  }
});
