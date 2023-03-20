"use strict";

{
    htmx.on(window, "load", function() {
        const elements = {};
        elements.selector = htmx.find("#header-image-selector");
        elements.selector_input = htmx.find(elements.selector, "input[type=hidden]");
        elements.selector_preview = htmx.find(elements.selector, "#header-image-selector-preview");
        elements.selector_dialogs = htmx.find(elements.selector, "#header-image-selector-dialogs");
        elements.selector_clear_button = htmx.find(elements.selector, "#header-image-selector-clear");

        const emptyImageDataUrl = elements.selector_clear_button.dataset.emptyImageDataUrl;

        const clear_header_image = function(event) {
            // Clear input value and preview URL
            elements.selector_input.value = null;
            elements.selector_preview.src = emptyImageDataUrl;
        }

        const handle_finalize_upload = function(event) {
            // Set input value and preview URL
            if (event.detail.file_type === "image") {
                elements.selector_input.value = event.detail.file_id;
                elements.selector_preview.src = event.detail.file_url;
            }

            // Destroy all dialogs
            if (event.detail.new_file === true) {
                elements.selector_dialogs.textContent = "";
            }
        }

        // Handle errors on the client side
        const clear_error_response = function(event) {
            const dialogErrorElement = htmx.find(elements.selector_dialogs, "#client-side-error");
            if (dialogErrorElement !== null) {
                dialogErrorElement.hidden = true;
            }
        }

        const handle_error_response = function(event) {
            if (event.detail.xhr.status === 413) {
                const dialogErrorElement = htmx.find(elements.selector_dialogs, "#client-side-error");
                if (dialogErrorElement === null) {
                    return;
                }

                let errorText;

                const maxContentSizeHeader = event.detail.xhr.getResponseHeader("Max-Content-Length");
                if (maxContentSizeHeader !== null) {
                    errorText = "Please upload a file smaller than " + maxContentSizeHeader + " in size.";
                }
                else {
                    errorText = "Please upload a file smaller in size.";
                }

                dialogErrorElement.textContent = errorText;
                dialogErrorElement.hidden = false;
            }
        }

        htmx.on(elements.selector, "finalizeUpload", handle_finalize_upload);
        htmx.on(elements.selector_clear_button, "click", clear_header_image);
        htmx.on(elements.selector, "htmx:beforeRequest", clear_error_response);
        htmx.on(elements.selector, "htmx:responseError", handle_error_response);
    });
}
