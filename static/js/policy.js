var iteration = 0;

function addAnotherPolicyService() {
    htmlPolicyService = `
        <div id="service${iteration}" class="form-group">
            <div class="form-inline">
                <label for="serviceIps">Service #${iteration + 1}: </label>
                <span>
                    <select class="form-control ml-3" id="serviceSelect${iteration}" name="services[${iteration}][service_id]" aria-describedby="serviceIps">
                    </select>
                </span>
            </div>
            <div class="form-inline mt-1 ml-3">
                <label class="mr-2">- Minimum Bandwidth:</label>
                    <input name="services[${iteration}][min_bandwidth]" class="form-control" type="number" min="0" max="20000000"
                    onkeypress="return (event.charCode == 8 || event.charCode == 0 || event.charCode == 13) ? null : event.charCode >= 48 && event.charCode <= 57"></input>
                    <div class="input-group-append">
                        <span class="input-group-text">kbps</span>
                    </div>  
            </div>
            <div class="form-inline mt-1 ml-3">
                <label class="mr-2">- Shape Bandwidth:</label>
                <input name="services[${iteration}][hard_bandwidth]" class="form-control" type="number" min="0" max="20000000"
                onkeypress="return (event.charCode == 8 || event.charCode == 0 || event.charCode == 13) ? null : event.charCode >= 48 && event.charCode <= 57"></input>
                <div class="input-group-append">
                    <span class="input-group-text">kbps</span>
                </div>
            </div>
            <div class="form-inline mt-1 ml-3">
                <label class="mr-2">- Mark Traffic with DSCP value:</label>
                <select name="services[${iteration}][mark_dscp]" class="form-control mr-1">
                    <option value="" selected>None</option>
                    <option value="0">0</option>
                    <option value="8">8</option>
                    <option value="10">10</option>
                    <option value="12">12</option>
                    <option value="14">14</option>
                    <option value="16">16</option>
                    <option value="18">18</option>
                    <option value="20">20</option>
                    <option value="22">22</option>
                    <option value="24">24</option>
                    <option value="26">26</option>
                    <option value="28">28</option>
                    <option value="30">30</option>
                    <option value="32">32</option>
                    <option value="34">34</option>
                    <option value="36">36</option>
                    <option value="38">38</option>
                    <option value="40">40</option>
                    <option value="46">46</option>
                    <option value="48">48</option>
                    <option value="56">56</option>                    
                </select>
            </div>
        </div>
    `;
    iteration++;
    document.getElementById("policyServices").insertAdjacentHTML("beforeend", htmlPolicyService);
    setServices();
    if (iteration == 1) {
        removeButton = `
            <button id="removeServiceButton" 
            onclick="removeLastPolicyService()" 
            type="button" class="ml-1 btn btn-danger btn-sm">
            Remove Last Service -
            </button>
            `;
        document.getElementById("serviceButtonGroup").insertAdjacentHTML("beforeend", removeButton);
    }
}

function removeLastPolicyService() {
    iteration--;
    serviceElement = document.getElementById(`service${iteration}`);
    serviceElement.parentNode.removeChild(serviceElement);

    if (iteration == 0) {
        removeButton = document.getElementById("removeServiceButton");
        removeButton.parentNode.removeChild(removeButton);
    }
}

function setServices(serviceSelect = null) {
    const Http = new XMLHttpRequest();
    const url = "/api/services";

    Http.open("GET", url, true);
    Http.onreadystatechange = function () {
        if (Http.readyState == 4 && Http.status == 200) {
            var services = JSON.parse(Http.response);
            if (serviceSelect != null) {
                insertServiceOptions(services, serviceSelect);
            } else {
                insertServiceOptions(
                    services,
                    document.getElementById(`serviceSelect${iteration - 1}`)
                );
            }
        }
    };
    Http.send();
}

function insertServiceOptions(services, serviceSelect) {
    serviceOptions = ``;
    for (const service of services) {
        serviceOptions += `
            <option value="${service.id}">${service.name}</option>
            `;
    }
    serviceSelect.insertAdjacentHTML("beforeend", serviceOptions);
}

function handleForm() {
    var policy = {
        name: document.getElementById("policyName").value,
        description: document.getElementById("policyDescription").value,
        services: [],
    };

    for (i = 0; i < iteration; i++) {
        service = {
            service_id: document.getElementsByName(`services[${i}][service_id]`)[0].value,
            min_bandwidth: document.getElementsByName(`services[${i}][min_bandwidth]`)[0].value,
            max_bandwidth: document.getElementsByName(`services[${i}][hard_bandwidth]`)[0].value,
            mark_dscp: document.getElementsByName(`services[${i}][mark_dscp]`)[0].value,
        };
        policy.services.push(service);
    }

    const Http = new XMLHttpRequest();
    const url = window.location.pathname;

    Http.open("POST", url, true);
    Http.setRequestHeader("Content-type", "application/json");
    Http.onreadystatechange = function () {
        if (Http.readyState == 4 && Http.status == 200) {
            window.location.replace(url.replace("/update", "").replace("/new", ""));
        } else {
            document.getElementById("errorAlert").innertHTML = `
            <div class="alert alert-dark alert-dismissible fade show" role="alert">
            <strong>Something went wrong!</strong>    
            <button type="button" class="close" data-dismiss="alert" aria-label="Close">
                    <span aria-hidden="true">&times;</span>
                </button>
            </div>
            `;
        }
    };
    console.log(JSON.stringify(policy));
    Http.send(JSON.stringify(policy));
}

function setIterationValue(value) {
    iteration = value;
    if (iteration > 0) {
        removeButton = `
            <button id="removeServiceButton" 
            onclick="removeLastPolicyService()" 
            type="button" class="ml-1 btn btn-danger btn-sm">
            Remove Last Service -
            </button>
            `;
        document.getElementById("serviceButtonGroup").insertAdjacentHTML("beforeend", removeButton);
    }

    for (i = 0; i < value; i++) {
        serviceSelect = document.getElementById(`serviceSelect${i}`);
        setServices(serviceSelect);
    }
}
