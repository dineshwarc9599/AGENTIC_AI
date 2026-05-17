// =====================================
// frontend/script.js
// =====================================

const API_URL =
    "http://127.0.0.1:8000/ask";

async function askQuestion() {

    const input =
        document.getElementById(
            "question-input"
        );

    const question =
        input.value.trim();

    if (!question) return;

    addUserMessage(question);

    input.value = "";

    addLoadingMessage();

    try {

        const response =
            await fetch(API_URL, {

                method: "POST",

                headers: {
                    "Content-Type":
                        "application/json"
                },

                body: JSON.stringify({
                    question: question
                })
            });

        const data =
            await response.json();

        removeLoadingMessage();

        addAIMessage(
            formatAnswer(data.answer)
        );

    } catch (error) {

        removeLoadingMessage();

        addAIMessage(
            "❌ Error connecting to backend."
        );

        console.error(error);
    }
}

/* Add User Message */

function addUserMessage(message) {

    const chatBox =
        document.getElementById(
            "chat-box"
        );

    const div =
        document.createElement("div");

    div.className =
        "user-message";

    div.innerText = message;

    chatBox.appendChild(div);

    scrollToBottom();
}

/* Add AI Message */

function addAIMessage(message) {

    const chatBox =
        document.getElementById(
            "chat-box"
        );

    const wrapper =
        document.createElement("div");

    wrapper.className =
        "ai-message";

    wrapper.innerHTML = `

        <div class="ai-label">
            AI Agent
        </div>

        <div class="message-content">
            ${message}
        </div>

    `;

    chatBox.appendChild(wrapper);

    scrollToBottom();
}

/* Loading Message */

function addLoadingMessage() {

    const chatBox =
        document.getElementById(
            "chat-box"
        );

    const div =
        document.createElement("div");

    div.className =
        "ai-message";

    div.id =
        "loading-message";

    div.innerHTML = `

        <div class="ai-label">
            AI Agent
        </div>

        <div class="message-content">
            ⏳ Thinking...
        </div>

    `;

    chatBox.appendChild(div);

    scrollToBottom();
}

/* Remove Loading */

function removeLoadingMessage() {

    const loading =
        document.getElementById(
            "loading-message"
        );

    if (loading) {

        loading.remove();
    }
}

/* Scroll */

function scrollToBottom() {

    const chatBox =
        document.getElementById(
            "chat-box"
        );

    chatBox.scrollTop =
        chatBox.scrollHeight;
}

/* Fill Sample Question */

function fillQuestion(button) {

    document.getElementById(
        "question-input"
    ).value = button.innerText;
}

/* Format Response */

function formatAnswer(answer) {

    if (
        typeof answer === "object"
    ) {

        return JSON.stringify(
            answer,
            null,
            2
        );
    }

    return answer
        .replace(/\n/g, "<br>");
}

/* Enter Key Support */

document
    .getElementById(
        "question-input"
    )
    .addEventListener(
        "keypress",
        function(event) {

            if (
                event.key === "Enter"
            ) {

                askQuestion();
            }
        }
    );