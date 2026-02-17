const backendElts = {
    popup: "backend-url-popup",
    error: "backend-url-error",
    input: "backend-url-input",
};
Object.keys(backendElts).forEach(
    key => backendElts[key] =
    document.getElementById(backendElts[key] == null ? key : backendElts[key]));

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

function askBackendUrl(error) {
    backendElts.popup.style = "";
    backendElts.error.textContent = error == null ? "" : error;
    backendElts.input.placeholder = backendUrl == null ?
        "Ex: http://127.0.0.1:8000" :
        backendUrl;

    onSetUrl = () => document.location.reload();
}

function setBackendUrl() {
    backendUrl = backendElts.input.value;
    localStorage.setItem("backend-url", backendElts.input.value);

    if (onSetUrl != null)
        onSetUrl();

    backendElts.popup.style = "display: none";
}
