"use strict";

{
    htmx.on(window, "load", function() {
        const elements = {};
        elements.editor = htmx.find("#markdown-editor");
        elements.editor_textarea = htmx.find(elements.editor, "textarea");
        elements.editor_preview = htmx.find(elements.editor, "#markdown-editor-preview");
        elements.editor_preview_switch = htmx.find(elements.editor, "#markdown-editor-preview-switch");
        elements.editor_image_selector = htmx.find(elements.editor, "#markdown-editor-image-selector")
        elements.editor_dialogs = htmx.find(elements.editor, "#markdown-editor-dialogs");

        const handle_editor_preview_switch_click = function(event) {
            if (elements.editor_preview.hidden) {
                // Show and load preview
                elements.editor_preview.hidden = false;
                htmx.trigger(elements.editor, "preview", {});

                // Hide other actions
                elements.editor_image_selector.hidden = true;
            }
            else {
                // Hide and clear preview
                elements.editor_preview.hidden = true;
                elements.editor_preview.textContent = "";

                // Show other actions
                elements.editor_image_selector.hidden = false;

                // Focus on textarea
                elements.editor_textarea.focus();
            }

            // Toggle icons
            htmx.toggleClass(elements.editor_preview_switch, "bi-search");
            htmx.toggleClass(elements.editor_preview_switch, "bi-markdown");
        }

        const handle_finalize_upload = function(event) {
            // Add content based on the type of the uploaded file
            if (event.detail.file_type === "image") {
                const altText = event.detail.metadata.alt;
                const fileUrl = event.detail.file_url;
                elements.editor_textarea.value += `\n\n![${altText}](${fileUrl})`;
            }

            // Destroy all dialogs
            if (event.detail.new_file === true) {
                elements.editor_dialogs.textContent = "";
            }

            // Focus on textarea
            elements.editor_textarea.focus();
        }

        // Handle errors on the client side
        const clear_error_response = function(event) {
            const dialogErrorElement = htmx.find(elements.editor_dialogs, "#client-side-error");
            if (dialogErrorElement !== null) {
                dialogErrorElement.hidden = true;
            }
        }

        const handle_error_response = function(event) {
            if (event.detail.xhr.status === 413) {
                const dialogErrorElement = htmx.find(elements.editor_dialogs, "#client-side-error");
                if (dialogErrorElement === null) {
                    return;
                }

                let errorText;

                const maxRequestContentLength = event.detail.xhr.getResponseHeader("Max-Request-Content-Length");
                if (maxRequestContentLength !== null) {
                    errorText = "Please upload a file smaller than " + maxRequestContentLength + " in size.";
                }
                else {
                    errorText = "Please upload a file smaller in size.";
                }

                dialogErrorElement.textContent = errorText;
                dialogErrorElement.hidden = false;
            }
        }

        htmx.on(elements.editor_preview_switch, "click", handle_editor_preview_switch_click);
        htmx.on(elements.editor, "finalizeUpload", handle_finalize_upload);
        htmx.on(elements.editor, "htmx:beforeRequest", clear_error_response);
        htmx.on(elements.editor, "htmx:responseError", handle_error_response);
    });

    htmx.onLoad(function(element) {
        if (element instanceof Element && element.id === "image-uploader-dialog") {
            const closeButton = htmx.find(element, "a.close");
            if (closeButton !== null) {
                htmx.on(closeButton, "click", function(event) {
                    event.preventDefault();
                    element.parentNode.removeChild(element);
                });
            }

            element.open = true;
        }
    });

    htmx.defineExtension("map-params", {
        onEvent: function(name, event) {
            if (name === "htmx:configRequest") {
                const elt = event.detail.elt;
                const attr_value = elt.getAttribute("map-params") || elt.getAttribute("data-map-params");
                if (attr_value === null) {
                    return;
                }

                const param_mappings = attr_value.split(",");
                for (let i = 0; i < param_mappings.length; i++) {
                    const param_mapping = param_mappings[i].split(":");
                    if (param_mapping.length === 2) {
                        const old_param = param_mapping[0].trim();
                        const new_param = param_mapping[1].trim();

                        const param_value = event.detail.parameters[old_param];
                        if (param_value !== undefined) {
                            event.detail.parameters[new_param] = param_value;
                            delete event.detail.parameters[old_param];
                        }
                    }
                }
            }
        }
    });
}
