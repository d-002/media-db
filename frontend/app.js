const elts = {
    globalTags: "global-tags",
    currentTags: "current-tags",
    currentName: "current-name",
    currentDate: "current-date",
    newTagName: "new-tag-name",
    content: null,
    prompt: null,
};

let tagElts = []; // [tag id: {global element, current element}]

const MAX_IMAGE_LENGTH = 30;
const PROMPT_N_RESULTS = 50;

let currentImage = null;

function globalTagClick(evt) {
    const eltType = evt.target.tagName.toUpperCase();
    if (eltType === "IMG") {
        // delete tag from database
        const ok = confirm("Sure you want to delete this tag from the database?");
        if (!ok)
            return;

        const tagId = evt.target.parentNode.getAttribute("tag-id");
        httpDelete("/tag/" + tagId + "/remove", [], updateGlobalTags);
    }
    else if (eltType == "SPAN") {
        // toggle tag
        evt.target.classList.toggle("selected");
    }
}

function currentTagClick(evt) {
    if (currentImage == null) {
        alert("Please select an image first.");
        return;
    }

    const eltType = evt.target.tagName.toUpperCase();
    const tagId = evt.target.getAttribute("tag-id");

    if (eltType == "SPAN") {
        const selected = evt.target.classList.toggle("selected");
        const action = selected ? "assign" : "unassign";

        httpPost("/" + action + "/" + currentImage.id + "/" + tagId, [], null, null);
    }
}

function updateGlobalTags(callback) {
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

        if (callback != null)
            callback();
    });
}

function updateCurrentTags(image) {
    const callback = currentTags => {
        currentTagIds = currentTags.map(tag => tag.id);
        Object.keys(tagElts).forEach(tagId => {
            tagId = parseInt(tagId);
            const classList = tagElts[tagId].current.classList;

            if (currentTagIds.includes(tagId))
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

function createNewTag() {
    const name = encodeURIComponent(elts.newTagName.value);
    httpPost("/tags/new?tag_name=" + name, [], null, () => {
        updateGlobalTags();
        updateCurrentTags();
        elts.newTagName.value = "";
    });
}

function uploadMedia() {
    // no file type checks, this is completely safe trust :)
    const input = document.createElement("input");
    input.type = "file";
    input.multiple = true;
    input.style = "width: 0; height: 0;"
    document.body.appendChild(input);
    input.click();
    input.addEventListener("change", () => {
        let count = 0;
        const targetCount = input.files.length;

        Array.from(input.files).forEach(file => {
            const timestamp = new Date(file.lastModified).getTime() / 1000;

            const formData = new FormData();
            formData.append("name", file.name);
            formData.append("timestamp", timestamp);
            formData.append("file", file);
            httpPost("/images/new", [], formData, () => {
                if (++count < targetCount)
                    return;

                // all files have been uploaded
                refreshAll();
            }, true);
        });

        input.remove();
    });
}

function searchWithPrompt() {
    const prompt = encodeURIComponent(elts.prompt.value);
    httpGet("/images/prompt?n=" + PROMPT_N_RESULTS + "&prompt=" + prompt, [], ids => {
        console.log(ids);
        elts.prompt.setAttribute("placeholder", elts.prompt.value);
        elts.prompt.value = "";
    });
}

function trashCurrent() {
}

function refreshAll() {
    updateGlobalTags(getImages);
}

Object.keys(elts).forEach(
    key => elts[key] = document.getElementById(elts[key] == null ? key : elts[key]));
elts.globalTags.addEventListener("click", globalTagClick);
elts.currentTags.addEventListener("click", currentTagClick);
refreshAll();
