//const backendUrl = prompt("Enter the URL to the backend:");
const backendUrl = "http://127.0.0.1:8000";

function formatArgs(args) {
    return args.length ? "?" + args.join("&") : "";
}

function httpGet(url, args, callback) {
    fetch(backendUrl + url + formatArgs(args), {
        method: "GET",
        headers: { 'Access-Control-Allow-Origin': true },
    }).then(response => {
        if (response.ok)
            response.json().then(callback);
        else
            alert("Error: " + response.statusText);
    });
}

function httpPost(url, callback, args, body) {
    fetch(backendUrl + url + formatArgs(args), {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: body,
    }).then(response => {
        if (response.ok)
            response.json().then(callback);
        else
            alert("Error: " + response.statusText);
    });
}

function httpDelete(url, args, callback) {
    fetch(backendUrl + url + formatArgs(args), {
        method: "DELETE",
    }).then(response => {
        if (response.ok)
            response.json().then(callback);
        else
            alert("Error: " + response.statusText);
    });
}
