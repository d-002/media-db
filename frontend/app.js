const elts = {
    globalTags: "global-tags",
    currentTags: "current-tags",
    currentName: "current-name",
    currentDate: "current-date",
    newTagName: "new-tag-name",
    right: null,
    content: null,
    prompt: null,
    date: null,
};

let tagElts = []; // {tag id: {global element, current element}, ...}

const MAX_IMAGE_LENGTH = 30;
const PROMPT_N_RESULTS = 50;
const TAG_SEARCH_RADIUS = 10;
const LEFT = 0, RIGHT = 1;
const TAG_SEARCH = 0, PROMPT = 1;

let currentImage = null;
let lastMove = RIGHT;
let searchMethod = TAG_SEARCH;
let prompt = "";
let imageList = [];
let lastScroll;

function globalTagClick(evt) {
    const eltType = evt.target.tagName.toUpperCase();
    if (eltType === "IMG") {
        // delete tag from database
        const ok = confirm("Really delete this tag?");
        if (!ok)
            return;

        const tagId = evt.target.parentNode.getAttribute("tag-id");
        httpDelete("/tag/" + tagId + "/delete", [], updateGlobalTags);
    }
    else if (eltType == "SPAN") {
        // toggle tag
        evt.target.classList.toggle("selected");
    }
}

function currentTagClick(evt) {
    if (currentImage == null) {
        alert("Please select media first.");
        return;
    }

    const eltType = evt.target.tagName.toUpperCase();
    const tagId = evt.target.getAttribute("tag-id");

    if (eltType == "SPAN") {
        const selected = evt.target.classList.toggle("selected");
        const action = selected ? "assign" : "unassign";

        httpPost("/" + action + "/" + currentImage.id + "/" + tagId,
            [], null, null);
    }
}

function findImageById(id) {
    return imageList.filter(image => image.id == id)[0];
}

function listClick(evt) {
    const eltType = evt.target.tagName.toUpperCase();
    const imageId = evt.target.getAttribute("image-id");

    if (eltType != "IMG")
        return;

    updateCurrentImage(findImageById(imageId));
}

function updateGlobalTags() {
    httpGet("/tags/list", [], json => {
        tagElts = [];
        elts.globalTags.innerHTML = "";
        elts.currentTags.innerHTML = "";

        json.sort((a, b) => a.name.toLowerCase().localeCompare(
            b.name.toLowerCase())).forEach(tag => {

                const globalSpan = document.createElement("SPAN");
                globalSpan.textContent = tag.name;
                globalSpan.innerHTML = globalSpan.textContent + `
                <img class="icon" src="images/cross.png" title="Delete tag">
                `;
                globalSpan.setAttribute("tag-id", tag.id);
                globalSpan.className = "tag";
                elts.globalTags.appendChild(globalSpan);

                const currentSpan = document.createElement("SPAN");
                currentSpan.textContent = tag.name;
                currentSpan.setAttribute("tag-id", tag.id);
                currentSpan.className = "tag";
                elts.currentTags.appendChild(currentSpan);

                tagElts[tag.id] = {global: globalSpan, current: currentSpan};
            });

        searchMethod = TAG_SEARCH;
        applySearch();
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
        elts.currentName.title = "";
        elts.currentDate.textContent = "";
    }
    else {
        elts.content.src = backendUrl + "/image/" + image.id + "/data";
        let name = image.path;
        if (name.length > MAX_IMAGE_LENGTH)
            name = "..." + name.substring(name.length - MAX_IMAGE_LENGTH + 3);
        const date = new Date(image.timestamp * 1000);

        elts.currentName.textContent = name;
        elts.currentName.title = image.path;
        elts.currentDate.textContent = date.toLocaleString();
    }

    updateCurrentTags(image);
    updateImageInList();
}

function sortList(list, targetTimestamp, useTimestampAbs) {
    // using lots of intermediaries for speed
    const values = list.map(
        image => {
            if (image.score != null)
                return -image.score;

            const dt = image.timestamp - targetTimestamp;
            return useTimestampAbs ? Math.abs(dt) : dt;
        });
    let i = 0;
    const indices = list.map(_ => i++);
    const indicesSorted = indices.sort((i, j) => values[i] - values[j]);
    return indicesSorted.map(i => list[i]);
}

function updateImageList(list) {
    // Add separators when this value changes significantly:
    // - tag search: every day
    // - prompt search: every 5% probability

    elts.right.innerHTML = "";

    imageList = sortList(list, 0, false);

    if (imageList.length == 0) {
        const span = document.createElement("SPAN");
        span.className = "separator";
        span.textContent = "No media.";
        elts.right.appendChild(span);
        return;
    }

    let prevValue = null;
    imageList.forEach(image => {
        const value = searchMethod == TAG_SEARCH ?
            Math.floor(image.timestamp / 86400) * 86400000 :
            Math.floor(image.score * 20) * 5;

        if (value != prevValue) {
            const span = document.createElement("SPAN");
            span.className = "separator";
            span.textContent = searchMethod == TAG_SEARCH ?
                new Date(value).toLocaleDateString() :
                value + "% confidence";
            elts.right.appendChild(span);

            prevValue = value;
        }

        const div = document.createElement("DIV");
        div.innerHTML = '<img src="' + backendUrl + "/image/" + image.id +
            '/data" image-id="' + image.id + '">';
        elts.right.appendChild(div);
    });
}

function scrollToMid(elt) {
    if (elt == null)
        return false;

    const midHeight = elt.getBoundingClientRect().top -
        elts.right.getBoundingClientRect().top +
        elt.offsetHeight / 2;
    const target = document.body.offsetHeight / 2;

    elts.right.scrollTop -= target - midHeight;
    return true;
}

function updateImageInList() {
    const id = currentImage == null ? -1 : currentImage.id;

    let elt = null;

    // set selected image border
    Array.from(elts.right.children).forEach(div => {
        if (div.tagName.toUpperCase() != "DIV")
            return;
        const img = div.children[0];

        if (img.getAttribute("image-id") == id + "") {
            img.classList.add("selected");
            elt = img;
        }
        else
            img.classList.remove("selected");
    });

    // scroll to element
    return scrollToMid(elt);
}

// update current image in a way that makes sense with the new search
function transitionCurrent() {
    // no image selected: select the "best" one
    if (currentImage == null) {
        updateCurrentImage(imageList[0]);
        return;
    }

    // image already in list: just update selection in list
    if (imageList.map(image => image.id).includes(currentImage.id)) {
        updateImageInList();
        return;
    }

    updateCurrentImage(imageList[0]);
}

function applySearch() {
    if (searchMethod == TAG_SEARCH) {
        const body = Object.keys(tagElts).filter(
            id => tagElts[id].global.classList.contains("selected"));

        httpPost("/images/filter", [], body, list => {
            // trim list if needed, preferable around previous selected image
            if (currentImage != null)
                list = sortList(list, currentImage.timestamp, true)
            list = list.slice(0, TAG_SEARCH_RADIUS);
            updateImageList(list);
            transitionCurrent();
        });
    }
    else if (searchMethod == PROMPT) {
        httpGet("/images/prompt?n=" + PROMPT_N_RESULTS + "&prompt=" + prompt,
            [], list => {
                updateImageList(list);
                transitionCurrent();
            });
    }
}

function applyTagFilters() {
    searchMethod = TAG_SEARCH;
    applySearch();
}

function emptyTagFilters() {
    Array.from(elts.globalTags.children).forEach(
        elt => elt.classList.remove("selected"));
}

function createNewTag() {
    const name = encodeURIComponent(elts.newTagName.value);
    httpPost("/tags/new?tag_name=" + name, [], null, () => {
        elts.newTagName.value = "";
        updateGlobalTags();
    });
}

function searchAround(id, callback) {
    const body = Object.keys(tagElts).filter(
        id => tagElts[id].global.classList.contains("selected"));

    httpPost("/images/around?image_id=" + id + "&n=" +
        TAG_SEARCH_RADIUS, [], body, list => {
            updateImageList(list);
            if (callback != null)
                callback();
        });
}

// If there is an available image loaded, go to it, otherwise query surrounding
// images to try to fetch the target one and call the function again.
// fromPrev is there to avoid infinite loops in case the target doesn't exist.
function nextTo(direction, fromPrev = false) {
    if (currentImage == null)
        return;

    const index = imageList.map(i => i.id).indexOf(currentImage.id);
    const target = index + direction;
    if (index == -1)
        return;

    if (target < 0 || target >= imageList.length) {
        if (fromPrev) {
            updateImageInList();
            return;
        }

        if (searchMethod == TAG_SEARCH)
            searchAround(currentImage.id, () => nextTo(direction, true));
        else
            return;
    }
    else
        updateCurrentImage(imageList[target]);
}

function prev() {
    lastMove = LEFT;
    return nextTo(-1);
}

function next() {
    lastMove = RIGHT;
    return nextTo(1);
}

function chooseDate() {
    const timestamp = new Date(elts.date.value).getTime() / 1000;
    httpGet("/images/date?timestamp=" + timestamp, [], image =>
        searchAround(image.id, () => updateCurrentImage(image))
    );
}

function uploadMedia() {
    // no file type checks, this is completely safe trust :)
    const input = document.createElement("INPUT");
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
    const value = elts.prompt.value.trim();
    if (value.length === 0)
        return;

    prompt = encodeURIComponent(elts.prompt.value);
    elts.prompt.setAttribute("placeholder", value);
    elts.prompt.value = "";

    currentImage = null; // force select the best match in upcoming transition
    searchMethod = PROMPT;
    applySearch();
}

function trashCurrent() {
    const ok = confirm("Really delete this image?");
    if (!ok)
        return;
    if (currentImage == null) {
        alert("Please select media first.");
        return;
    }

    httpDelete("/image/" + currentImage.id + "/delete", [], () => {
        if (lastMove == RIGHT)
            next();
        else
            prev();
    });
}

function syncDatabase() {
    const ok = confirm("Really force resync the database?\n" +
        "This will take some time.");
    if (!ok)
        return;

    httpGet("/sync", [], () => {
        updateGlobalTags();
    });
}

function listScroll() {
    const now = Date.now();

    if (now - lastScroll < 500)
        return;
    if (searchMethod == PROMPT)
        return;
    if (imageList.length == 0)
        return;

    prevIds = imageList.map(image => image.id);

    function callback() {
        elts.right.innerHeight; // trigger reflow

        // check if anything changed, otherwise do nothing
        let changed = false;
        imageList.forEach(image => {
            if (!prevIds.includes(image.id))
                changed = true;
        });
        if (!changed)
            return;

        // if auto scroll failed, the image is not in view: scroll to the middle
        if (!updateImageInList()) {
            elts.right.scrollTop = scrollMax / 2;
        }

        lastScroll = now;
    }

    const scroll = elts.right.scrollTop;
    // -1 as threshold
    const scrollMax = elts.right.scrollHeight - elts.right.offsetHeight - 1;

    if (scroll <= 0) {
        searchAround(imageList[0].id, callback);
    }
    if (scroll >= scrollMax) {
        searchAround(imageList[imageList.length - 1].id, callback);
    }
}

function movement(evt) {
    if (evt.target.tagName.toUpperCase() == "INPUT")
        return;

    switch(evt.key) {
        case "h":
        case "k":
        case "ArrowLeft":
        case "ArrowUp":
            prev();
            break;
        case "l":
        case "j":
        case "ArrowRight":
        case "ArrowDown":
            next();
            break;
    }
}

Object.keys(elts).forEach(
    key => elts[key] =
    document.getElementById(elts[key] == null ? key : elts[key]));

elts.globalTags.addEventListener("click", globalTagClick);
elts.currentTags.addEventListener("click", currentTagClick);
elts.right.addEventListener("click", listClick);
elts.right.addEventListener("scroll", listScroll);
document.body.addEventListener("keydown", movement);

getBackendUrl(updateGlobalTags); // this will cascade update everything
