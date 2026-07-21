const urlInput = document.getElementById("urlInput");
const addUrlButton = document.getElementById("addUrlButton");
const webList = document.getElementById("webList");

const messages = document.getElementById("messages");
const input = document.getElementById("messageInput");
const sendButton = document.getElementById("sendButton");

const documentsList = document.getElementById("documentsList");
const fileInput = document.getElementById("fileInput");
const dropZone = document.getElementById("dropZone");


// ======================================================
// Helpers
// ======================================================

function scrollBottom() {
    messages.scrollTop = messages.scrollHeight;
}

function formatSize(bytes) {

    if (bytes < 1024)
        return bytes + " B";

    if (bytes < 1024 * 1024)
        return (bytes / 1024).toFixed(1) + " KB";

    if (bytes < 1024 * 1024 * 1024)
        return (bytes / 1024 / 1024).toFixed(2) + " MB";

    return (bytes / 1024 / 1024 / 1024).toFixed(2) + " GB";

}


// ======================================================
// Chat
// ======================================================

function createMessage(role, text = "") {

    const div = document.createElement("div");

    div.classList.add("message");

    if (role === "user")
        div.classList.add("user-message");
    else
        div.classList.add("assistant-message");

    div.textContent = text;

    messages.appendChild(div);

    scrollBottom();

    return div;

}


async function animateMessage(element, text) {

    element.innerHTML = "";

    const cursor = document.createElement("span");

    cursor.className = "typing-cursor";

    cursor.innerHTML = "|";

    element.appendChild(cursor);

    const words = text.split(" ");

    let result = "";

    for (const word of words) {

        result += word + " ";

        element.innerHTML = result;

        element.appendChild(cursor);

        scrollBottom();

        await new Promise(resolve => setTimeout(resolve, 18));

    }

    cursor.remove();

}


async function sendMessage() {

    const text = input.value.trim();

    if (!text)
        return;

    createMessage("user", text);

    input.value = "";

    sendButton.disabled = true;

    const assistant = createMessage("assistant");

    try {

        const response = await fetch("/chat", {

            method: "POST",

            headers: {
                "Content-Type": "application/json"
            },

            body: JSON.stringify({
                message: text
            })

        });

        const data = await response.json();

        await animateMessage(assistant, data.answer);

    }

    catch (e) {

        assistant.textContent = "Server error.";

    }

    sendButton.disabled = false;

}


sendButton.onclick = sendMessage;

input.addEventListener("keydown", e => {

    if (e.key === "Enter" && !e.shiftKey) {

        e.preventDefault();

        sendMessage();

    }

});


// ======================================================
// History
// ======================================================

async function loadHistory() {

    const response = await fetch("/chat/history");

    const history = await response.json();

    console.log("HISTORY:", history);

    messages.innerHTML = "";

    for (const msg of history.messages) {

        createMessage(msg.role, msg.content);

    }

    scrollBottom();

}


// ======================================================
// Documents
// ======================================================

async function loadDocuments() {

    const response = await fetch("/documents");

    const documents = await response.json();

    console.log("DOCUMENTS:", documents);

    documentsList.innerHTML = "";

    for (const doc of documents.documents) {

        const card = document.createElement("div");

        card.className = "document-card";

        card.innerHTML = `

            <div class="document-name">

                ${doc.filename}

            </div>

            <div class="document-size">

                ${formatSize(doc.size)}

            </div>

            <button class="delete-document">

                Delete

            </button>

        `;

        card
            .querySelector("button")
            .onclick = async () => {

                if (!confirm("Delete document?"))
                    return;

                await fetch("/documents/" + encodeURIComponent(doc.filename), {

                    method: "DELETE"

                });

                loadDocuments();

            };

        documentsList.appendChild(card);

    }

}


// ======================================================
// Web links
// ======================================================


async function loadWebLinks() {

    const response = await fetch("/web");

    const data = await response.json();

    console.log("WEB LINKS:", data);


    webList.innerHTML = "";


    for (const url of data.documents) {


        const card = document.createElement("div");

        card.className = "document-card";


        card.innerHTML = `

            <div class="document-name">

                ${url}

            </div>


            <button class="delete-document">

                Delete

            </button>

        `;


        card
        .querySelector("button")
        .onclick = async () => {


            if (!confirm("Delete URL?"))
                return;


            await fetch("/web/remove", {

                method: "DELETE",

                headers: {

                    "Content-Type": "application/json"

                },

                body: JSON.stringify({

                    url:url

                })

            });


            loadWebLinks();


        };


        webList.appendChild(card);

    }


}

// ======================================================
// Upload
// ======================================================

async function upload(file) {

    const form = new FormData();

    form.append("file", file);

    await fetch("/documents/upload", {

        method: "POST",

        body: form

    });

    loadDocuments();

}


fileInput.onchange = () => {

    if (!fileInput.files.length)
        return;

    upload(fileInput.files[0]);

};


dropZone.onclick = () => {

    fileInput.click();

};


dropZone.addEventListener("dragover", e => {

    e.preventDefault();

    dropZone.classList.add("dragover");

});


dropZone.addEventListener("dragleave", () => {

    dropZone.classList.remove("dragover");

});


dropZone.addEventListener("drop", e => {

    e.preventDefault();

    dropZone.classList.remove("dragover");

    if (!e.dataTransfer.files.length)
        return;

    const file = e.dataTransfer.files[0];

    const ext = file.name.split(".").pop().toLowerCase();

    if (ext !== "pdf" && ext !== "txt") {

        alert("Only PDF and TXT files are allowed.");

        return;

    }

    upload(file);

});

async function addWebLink() {


    const url = urlInput.value.trim();


    if (!url)
        return;


    try {


        const response = await fetch("/web/add", {


            method:"POST",


            headers:{

                "Content-Type":"application/json"

            },


            body:JSON.stringify({

                url:url

            })


        });


        if (!response.ok) {

            alert("Failed to add URL");

            return;

        }


        urlInput.value = "";


        loadWebLinks();


    }

    catch(e){

        console.error(e);

        alert("Server error");

    }


}


addUrlButton.onclick = addWebLink;


urlInput.addEventListener(
    "keydown",
    e=>{

        if(e.key==="Enter"){

            addWebLink();

        }

    }
);


// ======================================================
// Init
// ======================================================

loadHistory();

loadDocuments();

loadWebLinks();