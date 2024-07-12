console.log("Just to prove script is working")

// {type: "updateMouth", size: 1, message: "string"} // Open
// {type: "updateMouth", size: 0, message: "string"} // Closed

var url = 'ws://localhost:8001/api'

let ws

function showMessage(message) {
    window.setTimeout(() => window.alert(message), 50);
}

function connect(){    
    ws = new WebSocket('ws://localhost:8001');

    ws.onopen = () => {
    console.log('WebSocket connection opened');
    };

    ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        console.log('Received data:', data);
        switch (data.type) {
            case 'updateMouth':
                setFrame(data.size);
                console.log(data.message)
                break;
            default:
                console.log(`There is no ${data.type} prepared.`)
        }
        ws.send(200);
        return false;
    };

    ws.onerror = (error) => {
        console.error('WebSocket error:', error);
    };

    ws.onclose = () => {
        console.log('WebSocket connection closed. Attempting to reconnect in 1 second...');
        setTimeout(connect, 1000); // Attempt to reconnect after 1 second
    };
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
connect();