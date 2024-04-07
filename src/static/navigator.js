let attributes = [];
for (const attribute in window.navigator) {
  attributes.push(attribute);
}
attributes.sort();
// Navigator
const navigator = document.getElementById("navigator");
// Create h1 element
const h1 = document.createElement("h1");
h1.innerText = "Navigator";
navigator.appendChild(h1);
// Create ul and li elements
const ul = document.createElement("ul");
// loop through windows.navigator object
attributes.forEach((attribute) => {
  if (typeof window.navigator[attribute] === "object") {
    return;
  } else if (typeof window.navigator[attribute] === "function") {
    return;
  }
  // create li element
  const li = document.createElement("li");
  // create span element
  const span_attribute = document.createElement("span");
  span_attribute.innerHTML = attribute;
  // create span element
  const span_value = document.createElement("span");
  span_value.innerHTML = window.navigator[attribute];
  // append span elements to li element
  li.appendChild(span_attribute);
  li.appendChild(span_value);
  // append li element to ul element
  ul.appendChild(li);
});
navigator.appendChild(ul);
