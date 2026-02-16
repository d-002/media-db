const elts = {
    globalTags: "global-tags",
    currentTags: "current-tags",
};

const backendCache = {
    globalTags: {}, // {id: {name: str, elt: span}}
};

const imageCache = new ImageCache();
let displayedImageId = null;

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

function fetchTags(callback) {
    httpGet("/tags/list", [], json => {
        backendCache.globalTags = {};

        let count = 0;
        const targetCount = Object.keys(json.tag_ids).length;

        // make a series of async calls and continue with the processing once
        // the right number of them succeededd
        json.tag_ids.forEach(id => {
            httpGet("/tag/" + id + "/info", [], tag => {
                backendCache.globalTags[id] = {name: tag["name"]};

                if (++count < targetCount)
                    return;

                elts.globalTags.innerHTML = "";

                Object.keys(backendCache.globalTags).sort((a, b) =>
                    backendCache.globalTags[a].name.toLowerCase().localeCompare(
                        backendCache.globalTags[b].name.toLowerCase()
                    )
                ).forEach(id => {
                    const name = backendCache.globalTags[id].name;

                    const span = document.createElement("span");
                    span.textContent = name;
                    span.innerHTML = span.textContent + `
                    <img class="icon" src="images/cross.png" title="Delete tag">
                    `;
                    span.setAttribute("tag-id", id);
                    span.className = "tag";
                    elts.globalTags.appendChild(span);
                    backendCache.globalTags[id].elt = span;
                });

                callback();
            });
        });
    });
}

function updateCurrentImage(id) {
    currentImageId = id;
    elts.
}

function updateRight() {
}

function getImages() {
    const body = Object.keys(backendCache.globalTags).filter(
        id => backendCache.globalTags[id].elt.classList.contains("selected"));

    httpPost("/images/filter", [], body, json => {
        if (json.image_ids.length === 0)
            elts.content.src = "images/placeholder.png";
        else if (!json.image_ids.contains(currentImageId))
            updateCurrentImage(json.image_ids[0]);

        json.image_ids.forEach(id => {
            imageCache.get(id, 
        });
    });
}

function applyTagFilters() {
    getImages();
}

function emptyTagFilters() {
    Array.from(elts.globalTags.children).forEach(elt => elt.classList.remove("selected"));
}

function clearTagFilters() {
    Array.from(elts.globalTags.children).forEach(elt => elt.classList.add("selected"));
}

function start() {
    fetchTags(getImages);
}

Object.keys(elts).forEach(key => elts[key] = document.getElementById(elts[key]));
elts.globalTags.addEventListener("click", globalTagClick);
elts.currentTags.addEventListener("click", currentTagClick);
start();
