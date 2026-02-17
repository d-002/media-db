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
    }).catch(askBackendUrl);
}

function httpPost(url, args, body, callback, isRaw = false) {
    data = {
        method: "POST",
    };
    if (isRaw)
        data.body = body;
    else {
        data.body = body == null ? null : JSON.stringify(body);
        data.headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
        };
    }

    fetch(backendUrl + url + formatArgs(args), data).then(response => {
        if (response.ok)
            response.json().then(callback);
        else
            alert("Error: " + response.statusText);
    }).catch(askBackendUrl);
}

function httpDelete(url, args, callback) {
    fetch(backendUrl + url + formatArgs(args), {
        method: "DELETE",
    }).then(response => {
        if (response.ok)
            response.json().then(callback);
        else
            alert("Error: " + response.statusText);
    }).catch(askBackendUrl);
}
