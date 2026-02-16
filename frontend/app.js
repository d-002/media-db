const elts = {
    globalTags: "global-tags",
    currentTags: "current-tags",
};

const cache = {
    globalTags: {},
};

function globalTagClick(evt) {
    const tagName = evt.target.tagName.toUpperCase();
    if (tagName === "IMG") {
        // delete tag from database
        const ok = confirm("Sure you want to delete this tag from the database?");
        if (!ok)
            return;

        const id = evt.target.parentNode.getAttribute("tag-id");
        httpDelete("/tag/" + id + "/remove", [], fetchTags);
    }
    else if (tagName == "SPAN") {
        // toggle tag
        evt.target.classList.toggle("selected");
    }
}

function currentTagClick(evt) {
    const tagName = evt.target.tagName.toUpperCase();
    if (tagName == "SPAN") {
        evt.target.classList.toggle("selected");
        // TODO
    }
}

function fetchTags() {
    httpGet("/tags/list", [], json => {
        cache.globalTags = {};

        let count = 0;
        const targetCount = Object.keys(json.tag_ids).length;

        // make a series of async calls and continue with the processing once
        // the right number of them succeededd
        json.tag_ids.forEach(id => {
            httpGet("/tag/" + id + "/info", [], tag => {
                cache.globalTags[id] = tag["name"];

                if (++count < targetCount)
                    return;

                elts.globalTags.innerHTML = "";

                Object.keys(cache.globalTags).sort((a, b) =>
                    cache.globalTags[a].toLowerCase().localeCompare(
                        cache.globalTags[b].toLowerCase()
                    )
                ).forEach(id => {
                    const name = cache.globalTags[id];

                    const span = document.createElement("span");
                    span.textContent = name;
                    span.innerHTML = span.textContent + `
                    <img class="icon" src="images/cross.png" title="Delete tag">
                    `;
                    span.setAttribute("tag-id", id);
                    span.className = "tag selected";
                    elts.globalTags.appendChild(span);
                });
            });
        });
    });
}

function start() {
    fetchTags();
}

Object.keys(elts).forEach(key => elts[key] = document.getElementById(elts[key]));
elts.globalTags.addEventListener("click", globalTagClick);
elts.currentTags.addEventListener("click", currentTagClick);
start();
