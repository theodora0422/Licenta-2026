let monacoEditorInstance = null;

function initializeCodeInput() {
    if (typeof require === "undefined") {
        console.error("Monaco loader is not available.");
        return;
    }

    require.config({
        paths: {
            vs: "https://cdnjs.cloudflare.com/ajax/libs/monaco-editor/0.52.2/min/vs"
        }
    });

    require(["vs/editor/editor.main"], function () {
        const editorContainer = document.getElementById("editor-container");

        if (!editorContainer) {
            console.error("Editor container not found.");
            return;
        }

        monacoEditorInstance = monaco.editor.create(editorContainer, {
            value:
`public class Example {
    public static void main(String[] args) {
        Object lockA = new Object();
        Object lockB = new Object();
    }
}`,
            language: "java",
            theme: "vs",
            automaticLayout: true,
            minimap: {
                enabled: false
            },
            fontSize: 14,
            scrollBeyondLastLine: false,
            tabSize: 4
        });

        console.log("Code input module initialized.");
    });
}

function getSourceCode() {
    if (!monacoEditorInstance) {
        return "";
    }

    return monacoEditorInstance.getValue();
}

window.CodeInputModule = {
    initializeCodeInput,
    getSourceCode
};