console.log("Just to prove script is working")

// {type: "updateMouth", size: 1, message: "string"} // Open
// {type: "updateMouth", size: 0, message: "string"} // Closed

function showMessage(message) {
    window.setTimeout(() => window.alert(message), 50);
}

function receiveMoves(board, websocket) {
    websocket.addEventListener("message", ({ data}) => {
        const event = JSON.parse(data);
        switch (event.type) {
            case "updateMouth":
                // Update Dabi.
                updateImage(event.size)
                break;
            case "error":
                showMessage(event.message);
                break;
            default:
                throw new Error(`Unsupported event type: ${event.type}.`);
        }
    });
}


// Everything below this is for 2 frame Dabi
function setFrame(frame) {
    console.log('set frame', frame);
    resetFrames();

    document.querySelectorAll('img')[frame - 1].style.display = 'block';

}

function resetFrames() {
    document.querySelectorAll('img').forEach(function (entry) {
        entry.style.display = 'none';
    });
}

setFrame(1);