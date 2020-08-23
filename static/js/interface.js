var iteration = 0

function deleteSchedule(){
    if (iteration > 0) {
        document.getElementById("divSchedule" + (iteration-1)).remove()
        iteration -= 1
    }
}

function addSchedule() {
    if (iteration < 10) {
        divSchedules = document.getElementById('schedules')
        rawHTML = 
        `
        <div id="divSchedule${iteration}" class="form-inline">
            <div class="ml">
                <div>
                    Day<br>
                    <select name="policySchedules[${iteration}][day]" class="form-control">
                        <option value="monday" selected>Monday</option>
                        <option value="tuesday">Tuesday</option>
                        <option value="wednesday">Wednesday</option>
                        <option value="thursday">Thursday</option>
                        <option value="friday">Friday</option>
                        <option value="saturday">Saturday</option>
                        <option value="sunday">Sunday</option>
                    </select>
                </div>
            </div>
            <div class="ml">
                <div>
                    Time<br>
                    <input name="policySchedules[${iteration}][time]" type="time" class="form-control"></input>
                </div>
            </div>
            <div class="ml">
                <div>
                    Policy<br>
                    <select id="policyScheduleSelect${iteration}" name="policySchedules[${iteration}][policy]" class="form-control">
                    </select>
                </div>
            </div>
        </div>
        `
        divSchedules.insertAdjacentHTML("beforeend", rawHTML);
        setPolicies(document.getElementById(`policyScheduleSelect${iteration}`))
        iteration += 1
    }
}

function setPolicies(policySelect = null) {
    const Http = new XMLHttpRequest();
    const url = "/api/policies";

    Http.open("GET", url, true);
    Http.onreadystatechange = function () {
        if (Http.readyState == 4 && Http.status == 200) {
            var policies = JSON.parse(Http.response);
            if (policySelect != null) {
                insertPolicyOptions(policies, policySelect);
            } else {
                insertPolicyOptions(policies, document.getElementById(`policySelect`));
            }
        }
    };
    Http.send();
}

function insertPolicyOptions(policies, policySelect) {
    policyOptions = ``;
    for (const policy of policies) {
        policyOptions += `
            <option value="${policy.id}">${policy.name}</option>
            `;
    }
    policySelect.insertAdjacentHTML("beforeend", policyOptions);
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
            policy_schedules: []
        };
    
        for (i = 0; i < iteration; i++) {
            policySchedule = {
                day: document.getElementsByName(`policySchedules[${i}][day]`)[0].value,
                time: document.getElementsByName(`policySchedules[${i}][time]`)[0].value,
                policy_id: document.getElementsByName(`policySchedules[${i}][policy]`)[0].value,
            };
            interface_data.policy_schedules.push(policySchedule);
        }
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
