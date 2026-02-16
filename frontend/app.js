const elts = {
    globalTags: "global-tags",
    currentTags: "current-tags",
    currentName: "current-name",
    currentDate: "current-date",
    content: null,
};

const backendCache = {
    globalTags: [], // {id: {tag, elt}}
};

const MAX_IMAGE_LENGTH = 30;

let currentImage = null;

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
        backendCache.globalTags = [];
        elts.globalTags.innerHTML = "";

        json.sort((a, b) => a.name.toLowerCase().localeCompare(b.name.toLowerCase())).forEach(tag => {
            const span = document.createElement("span");
            span.textContent = tag.name;
            span.innerHTML = span.textContent + `
            <img class="icon" src="images/cross.png" title="Delete tag">
            `;
            span.setAttribute("tag-id", tag.id);
            span.className = "tag";
            elts.globalTags.appendChild(span);
            backendCache.globalTags[tag.id] = {tag: tag, elt: span};
        });

        callback();
    });
}

function updateCurrentImage(image) {
    currentImage = image;
    if (image == null) {
        elts.content.src = "images/placeholder.png";
        elts.currentName.textContent = "No image selected.";
        elts.currentDate.textContent = "";
    }
    else {
        elts.content.src = backendUrl + "/image/" + image.id + "/data";
        let name = image.path;
        if (name.length > MAX_IMAGE_LENGTH)
            name = "..." + name.substring(name.length - MAX_IMAGE_LENGTH + 3);
        elts.currentName.textContent = name;
        const date = new Date(image.timestamp * 1000);
        elts.currentDate.textContent = date.toLocaleString();
    }
}

function updateRight() {
}

function getImages() {
    const body = Object.keys(backendCache.globalTags).filter(
        id => backendCache.globalTags[id].elt.classList.contains("selected"));

    httpPost("/images/filter", [], body, json => {
        if (json.length === 0)
            updateCurrentImage(null);
        else if (!json.includes(currentImage))
            updateCurrentImage(json[0]);
    });
}

function applyTagFilters() {
    getImages();
}

function emptyTagFilters() {
    Array.from(elts.globalTags.children).forEach(elt => elt.classList.remove("selected"));
}

function start() {
    fetchTags(getImages);
}

Object.keys(elts).forEach(
    key => elts[key] = document.getElementById(elts[key] == null ? key : elts[key]));
elts.globalTags.addEventListener("click", globalTagClick);
elts.currentTags.addEventListener("click", currentTagClick);
start();
