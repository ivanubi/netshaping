function tryDeviceConnection(host, ssh_username, ssh_password) {
    setLoadingStatusToDeviceConnection();

    var credentials = {
        host: host,
        ssh_username: ssh_username,
        ssh_password: ssh_password,
    };

    sendCredentials(credentials);
}

function tryDeviceConnectionFromForm() {
    setLoadingStatusToDeviceConnection();

    var credentials = {
        host: document.getElementById("deviceHost").value,
        ssh_username: document.getElementById("deviceUser").value,
        ssh_password: document.getElementById("devicePassword").value,
    };
    console.log(credentials);
    sendCredentials(credentials);
}

function sendCredentials(credentials) {
    const Http = new XMLHttpRequest();
    const url = "/devices/test_connection";
    Http.open("POST", url, true);
    Http.setRequestHeader("Content-type", "application/json");
    Http.onreadystatechange = function () {
        if (Http.readyState == 4 && Http.status == 200) {
            var response = Http.responseText;
            if (response == "success") {
                html_feedback = "<span class='text-success'>Success!</span>";
            } else if (response == "failed_authentication") {
                html_feedback = "<span class='text-warning'>Authentication Error</span>";
            } else {
                html_feedback = "<span class='text-warning'>Unreachable</span>";
            }
            document.getElementById("connectionStatus").innerHTML = html_feedback;
        }
    };
    Http.send(JSON.stringify(credentials));
}

function setLoadingStatusToDeviceConnection() {
    document.getElementById("connectionStatus").innerHTML = `
    <img src="/static/images/loading4.svg" width="20"></img><small> Connecting</small> 
    `;
}

function updateDeviceInterfaces(device_id) {
    document.getElementById("checkNewInterfacesStatus").innerHTML = `
    <img src="/static/images/loading4.svg" width="20"></img><small> Importing</small> 
    `;
    var device = { id: device_id };

    const Http = new XMLHttpRequest();
    const url = "/devices/update_interfaces";
    Http.open("POST", url, true);
    Http.setRequestHeader("Content-type", "application/json");
    Http.onreadystatechange = function () {
        if (Http.readyState == 4 && Http.status == 200) {
            var response = Http.responseText;
            if (response == "added_new_one") {
                window.location.replace(
                    `/devices/${device_id}?feedback=${encodeURI("Success! New interfaces added")}`
                );
            } else if (response == "failed_authentication") {
                window.location.replace(
                    `/devices/${device_id}?feedback=${encodeURI(
                        "Error! Failed SSH Authentication to the device"
                    )}`
                );
            } else if (response == "timeout") {
                window.location.replace(
                    `/devices/${device_id}?feedback=${encodeURI(
                        "Error! A connection could not be established"
                    )}`
                );
            } else {
                window.location.replace(
                    `/devices/${device_id}?feedback=${encodeURI("There are no new interfaces")}`
                );
            }
        }
    };
    Http.send(JSON.stringify(device));
}
