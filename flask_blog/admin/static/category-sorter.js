"use strict";

{
    let sortable = undefined;

    htmx.onLoad(function(content) {
        const sortable_categories = htmx.find(content, "#sortable-categories");

        sortable = Sortable.create(sortable_categories, {
            animation: 200,
            ghostClass: "ghost",
            handle: ".category-handle"
        });
    });

    htmx.on("htmx:beforeRequest", function(event) {
        if (sortable !== undefined) {
            sortable.option("disabled", true);
        }
    });

    htmx.on("htmx:afterRequest", function(event) {
        if (sortable !== undefined) {
            sortable.option("disabled", false);
        }
    });
}
