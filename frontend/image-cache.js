// images cache
class Image {
    constructor(id) {
        this.id = id;
        this.data = null;
        this.access();
    }

    access() {
        this.accessDate = Date.now();
    }

    load(callback) {
        httpGet("/image/" + this.id + "/data", [], data => {
            this.data = data;
            callback(this.data);
        });
    }
}

class ImageCache {
    constructor(length = 100) {
        this.length = length;
        this.images = {};
    }

    add(id, callback) {
        while (Object.keys(this.images).length >= this.length) {
            const oldest = this.images.reduce(
                (prev, curr) => prev.accessDate < curr.accessDate ? prev : curr
            );

            this.images.remove(oldest);
        }

        const image = new Image(id);
        this.images.push(image);
        image.load(callback);
    }

    get(id, callback) {
        const cached = this.images[id];
        if (cached == null)
            this.add(id, callback);
        else {
            cached.access();
            callback(cached.data);
        }
    }
}
