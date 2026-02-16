const elts = {
    globalTags: "global-tags",
    currentTags: "current-tags",
    currentName: "current-name",
    currentDate: "current-date",
    content: null,
};

let tagElts = []; // [tag id: {global element, current element}]

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
        tagElts = [];
        elts.globalTags.innerHTML = "";
        elts.currentTags.innerHTML = "";

        json.sort((a, b) => a.name.toLowerCase().localeCompare(b.name.toLowerCase())).forEach(tag => {
            const globalSpan = document.createElement("span");
            globalSpan.textContent = tag.name;
            globalSpan.innerHTML = globalSpan.textContent + `
            <img class="icon" src="images/cross.png" title="Delete tag">
            `;
            globalSpan.setAttribute("tag-id", tag.id);
            globalSpan.className = "tag";
            elts.globalTags.appendChild(globalSpan);

            const currentSpan = document.createElement("span");
            currentSpan.textContent = tag.name;
            currentSpan.setAttribute("tag-id", tag.id);
            currentSpan.className = "tag";
            elts.currentTags.appendChild(currentSpan);

            tagElts[tag.id] = {global: globalSpan, current: currentSpan};
        });

        callback();
    });
}

function updateCurrentTags(image) {
    const callback = currentTags => {
        currentTagIds = currentTags.map(tag => tag.id);
        Object.keys(tagElts).forEach(tag_id => {
            tag_id = parseInt(tag_id);
            const classList = tagElts[tag_id].current.classList;

            if (currentTagIds.includes(tag_id))
                classList.add("selected");
            else
                classList.remove("selected");
        });
    }

    if (image == null)
        callback([]);
    else
        httpGet("/image/" + image.id + "/tags", [], callback);
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

    updateCurrentTags(image);
}

function updateRight() {
}

function getImages() {
    const body = Object.keys(tagElts).filter(
        id => tagElts[id].global.classList.contains("selected"));

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
