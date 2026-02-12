// ===============================
// GLOBAL STATE
// ===============================
let questions = [];
let currentQuestion = 0;
let answers = {};
let isLocked = false;


// ===============================
// LOAD QUESTIONS
// ===============================
document.addEventListener("DOMContentLoaded", () => {
    currentQuestion = 0;
    answers = {};
    isLocked = false;

    fetch("/api/questions")
        .then(res => res.json())
        .then(data => {
            questions = data;
            loadQuestion();
        })
        .catch(err => {
            console.error("Failed to load questions:", err);
            alert("Unable to load questions.");
        });
});


// ===============================
// LOAD QUESTION
// ===============================
function loadQuestion() {
    const q = questions[currentQuestion];
    if (!q) return;

    document.getElementById("question").innerText =
        `(${currentQuestion + 1}/${questions.length}) ${q.question}`;

    const optionsDiv = document.getElementById("options");
    optionsDiv.innerHTML = "";
    isLocked = false;

    // ===============================
    // SELECT TYPE (BUTTONS)
    // ===============================
    if (q.type === "select" || q.options) {
        q.options.forEach(opt => {
            const btn = document.createElement("button");
            btn.innerText = opt.label;
            btn.className = "option-btn";

            btn.onclick = () => selectAnswer(q.key, opt.value);

            optionsDiv.appendChild(btn);
        });
    }

    // ===============================
    // NUMBER INPUT TYPE
    // ===============================
    else if (q.type === "number") {
        const input = document.createElement("input");
        input.type = "number";
        input.placeholder = q.placeholder || "Enter value";
        input.className = "number-input";

        const nextBtn = document.createElement("button");
        nextBtn.innerText = "Next";
        nextBtn.className = "option-btn";

        nextBtn.onclick = () => {
            if (input.value === "") {
                alert("Please enter a value");
                return;
            }
            selectAnswer(q.key, parseFloat(input.value));
        };

        optionsDiv.appendChild(input);
        optionsDiv.appendChild(nextBtn);
    }
}


// ===============================
// SAVE ANSWER & MOVE NEXT
// ===============================
function selectAnswer(key, value) {
    if (isLocked) return;
    isLocked = true;

    answers[key] = value;
    console.log("ANSWER SAVED:", answers);

    currentQuestion++;

    setTimeout(() => {
        if (currentQuestion < questions.length) {
            loadQuestion();
        } else {
            submitAssessment();
        }
    }, 200);
}


// ===============================
// SUBMIT TO BACKEND
// ===============================
function submitAssessment() {
    console.log("FINAL ANSWERS:", answers);

    fetch("/submit_assessment", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify(answers)
    })
    .then(res => res.json())
    .then(data => {
        answers = {};
        currentQuestion = 0;
        isLocked = false;

        if (data.redirect) {
            window.location.href = data.redirect;
        } else {
            alert("Unexpected response from server");
        }
    })
    .catch(err => {
        console.error("Submission failed:", err);
        alert("Something went wrong. Try again.");
    });
}
