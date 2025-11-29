let currentSessionId = null;

function setSessionId(id) {
    currentSessionId = id;
    const hidden = document.getElementById("session_id_input");
    if (hidden) hidden.value = id;
    enableStudyButtons();
}

function enableStudyButtons() {
    if (!currentSessionId) return;

    const summaryBtn = document.getElementById("btn-summary");
    const keyBtn     = document.getElementById("btn-keyterms");
    const qBtn       = document.getElementById("btn-questions");
    const rBtn       = document.getElementById("btn-resources");

    [summaryBtn, keyBtn, qBtn, rBtn].forEach(btn => btn.disabled = false);

    summaryBtn.setAttribute("hx-get", `/summary/${currentSessionId}`);
    keyBtn.setAttribute("hx-get", `/keyterms/${currentSessionId}`);
    qBtn.setAttribute("hx-get", `/questions/${currentSessionId}`);
    rBtn.setAttribute("hx-get", `/resources/${currentSessionId}`);
}

document.body.addEventListener("htmx:afterSettle", function () {
    // Look for the element *inside* #materials-panel that has data-session-id
    const sidElem = document.querySelector("#materials-panel [data-session-id]");
    const sid = sidElem ? sidElem.getAttribute("data-session-id") : null;

    if (sid && sid !== currentSessionId) {
        setSessionId(sid);
    }
});

// recording JS:
let mediaRecorder = null;
let recordedChunks = [];

const recordBtn = document.getElementById("record-btn");
const recordStatus = document.getElementById("record-status");

recordBtn.addEventListener("click", async () => {
    if (!mediaRecorder || mediaRecorder.state === "inactive") {
        try {
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            mediaRecorder = new MediaRecorder(stream);
            recordedChunks = [];

            mediaRecorder.ondataavailable = (e) => {
                if (e.data.size > 0) recordedChunks.push(e.data);
            };

            mediaRecorder.onstop = async () => {
                const blob = new Blob(recordedChunks, { type: "audio/webm" });
                await uploadLiveAudio(blob);
                stream.getTracks().forEach(t => t.stop());
                recordStatus.textContent = "Recording finished. Transcribing...";
            };

            mediaRecorder.start();
            recordBtn.textContent = "⏹ Stop Recording";
            recordStatus.textContent = "Recording...";
        } catch (err) {
            console.error(err);
            alert("Could not access microphone.");
        }
    } else if (mediaRecorder.state === "recording") {
        mediaRecorder.stop();
        recordBtn.textContent = "🎙 Start Recording";
    }
});

async function uploadLiveAudio(blob) {
    const formData = new FormData();
    formData.append("audio", blob, "live_recording.webm");
    if (currentSessionId) {
        formData.append("session_id", currentSessionId);
    }

    const resp = await fetch("/upload_live_audio", {
        method: "POST",
        body: formData
    });

    const html = await resp.text();
    document.getElementById("materials-panel").innerHTML = html;
    recordStatus.textContent = "Live audio processed.";
}
