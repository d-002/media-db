const backendUrlPopup = document.getElementById("backend-url-popup");
const backendUrlInput = document.getElementById("backend-url-input");

let backendUrl;
let onSetUrl = null;

function getBackendUrl(callback) {
    backendUrl = localStorage.getItem("backend-url");

    if (backendUrl == null) {
        askBackendUrl();
        onSetUrl = callback;
    }
    else
        callback();
}

function askBackendUrl() {
    backendUrlPopup.style = "";
    backendUrlInput.placeholder = backendUrl == null ?
        "Ex: http://127.0.0.1:8000" :
        backendUrl;

    onSetUrl = () => document.location.reload();
}

function setBackendUrl() {
    backendUrl = backendUrlInput.value;
    localStorage.setItem("backend-url", backendUrlInput.value);

    if (onSetUrl != null)
        onSetUrl();

    backendUrlPopup.style = "display: none";
}
