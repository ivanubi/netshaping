function setPolicies(policySelect = null) {
    const Http = new XMLHttpRequest();
    const url = "/api/policies";

    Http.open("GET", url, true);
    Http.onreadystatechange = function () {
        if (Http.readyState == 4 && Http.status == 200) {
            var policies = JSON.parse(Http.response);
            if (policySelect != null) {
                insertServiceOptions(policies, policySelect);
            } else {
                insertServiceOptions(policies, document.getElementById(`policySelect`));
            }
        }
    };
    Http.send();
}

function setPolicyToInt(device_id) {
    try {
        submitButton = document.getElementById("submitButton");
        submitButton.innerHTML = `
        <img src="/static/images/loading4.svg" width="20"></img> Applying changes
        `;
        const Http = new XMLHttpRequest();
        const url = `/api/interfaces/${device_id}/update`;
        var interface_data = {
            id: device_id,
            description: document.getElementById("description").value,
            policy_id: document.getElementById("policy_id").value,
            bandwidth: document.getElementById("bandwidth").value,
        };
        console.log(interface_data);

        Http.open("POST", url, true);
        Http.setRequestHeader("Content-type", "application/json");
        Http.responseType = "json";
        Http.onreadystatechange = function () {
            if (Http.readyState == 4 && Http.status == 200) {
                var response = Http.response;
                console.log(response);
                if (response.status == "success") {
                    html_alert = `
                    <div class="alert alert-success alert-dismissible fade show text-light" role="alert">
                    <strong>Success!</strong> ${response.response}. 
                    <a type="button" data-toggle="modal" class="btn btn-link btn-sm" data-target="#commandsModal">
                        See the commands used
                    </a>
                    <button type="button" class="close" data-dismiss="alert" aria-label="Close">
                        <span aria-hidden="true">&times;</span>
                    </button>
                    </div>`;

                    document.getElementById(
                        "commandsModalBody"
                    ).innerHTML = response.commands.toString().replace(/,/g, "<br>");
                } else {
                    html_alert = `
                    <div class="alert alert-warning alert-dismissible fade show" role="alert">
                    <strong>Error!</strong> ${response.response}.`
                    if (response.commands) {
                        document.getElementById(
                            "commandsModalBody"
                        ).innerHTML = response.commands.toString().replace(/,/g, "<br>");
                        html_alert += 
                            `
                            <a type="button" data-toggle="modal" class="btn btn-link btn-sm" data-target="#commandsModal">
                            See the commands that NetShaping tried to configure
                            </a>
                            `
                    }
                    html_alert +=
                    `
                    <button type="button" class="close" data-dismiss="alert" aria-label="Close">
                        <span aria-hidden="true">&times;</span>
                    </button>
                    </div>
                    `;
                }
                document.getElementById("alert").innerHTML = html_alert;
                submitButton.innerHTML = `Send Settings to the Interface`;
            } else {
                submitButton.innerHTML = `Send Settings to the Interface`;
            }
        };
        Http.send(JSON.stringify(interface_data));
    } catch (err) {
        document.getElementById("alert").innerHTML = `
        <div class="alert alert-warning alert-dismissible fade show" role="alert">
        <strong>Error!</strong> ${err.message}.
        <button type="button" class="close" data-dismiss="alert" aria-label="Close">
            <span aria-hidden="true">&times;</span>
        </button>
        </div>`;
        submitButton.innerHTML = `An issue was raised`;
    }
}
