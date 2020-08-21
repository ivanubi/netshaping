import sys
import pathlib

sys.path.append(str(pathlib.Path().absolute()))

from app import app, login_manager
from flask import request, render_template, redirect, url_for, jsonify, flash
import json

from models import *
from flask_login import login_required, logout_user, current_user, login_user
from datetime import date, datetime, timedelta
from sqlalchemy import func


@app.route("/login/", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("devices"))

    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]
        user = User.query.filter_by(email=email).first()
        if user and user.check_password(password=password):
            login_user(user)
            next_page = request.args.get("next")
            return redirect(next_page or url_for("devices"))
        flash("Invalid username/password combination")
        return redirect(url_for("login"))

    return render_template("login.html")


@app.route("/logout/")
@login_required
def logout():
    logout_user()
    return redirect(url_for("login"))


@login_manager.user_loader
def load_user(user_id):
    if user_id is not None:
        return User.query.get(user_id)
    return None


@login_manager.unauthorized_handler
def unauthorized():
    return redirect(url_for("login"))


"""
DEVICES VIEWS
"""


@app.route("/")
@app.route("/devices/", methods=["GET"])
@app.route("/devices/<id>", methods=["GET"])
@login_required
def devices(id=None):
    if id:
        feedback = (
            request.args.get("feedback") if request.args.get("feedback") else None
        )
        device = Device.query.get(int(id))
        title = "%r | Devices " % device.name
        return render_template(
            "devices/show.html",
            title=title,
            device=device,
            feedback=feedback,
            current_user=current_user,
        )
    else:
        title = "Devices"
        return render_template(
            "devices/index.html",
            title=title,
            devices=Device.query.all(),
            current_user=current_user,
        )


@app.route("/devices/new/", methods=["GET", "POST"])
@login_required
def new_device():
    try:
        title = "New | Devices"
        if request.method == "POST":
            new_device = Device(
                name=request.form["deviceName"],
                description=request.form["deviceDescription"],
                host=request.form["deviceHost"].replace(" ", ""),
                ssh_username=request.form["deviceUser"].replace(" ", ""),
                ssh_password=request.form["devicePassword"],
            )
            error = new_device.validate()
            if error:
                return render_template(
                    "devices/new.html",
                    device=new_device,
                    error=error,
                    title=title,
                    current_user=current_user,
                )
            else:
                new_device.create()
                return redirect(url_for("devices", id=new_device.id))
        else:
            return render_template(
                "devices/new.html",
                device=Device(),
                title=title,
                current_user=current_user,
            )
    except:
        error = "An issue was raised, IP entered might belong to an existing device"
        return render_template(
            "devices/new.html",
            device=new_device,
            error=error,
            title=title,
            current_user=current_user,
        )


@app.route("/devices/<id>/update", methods=["GET", "POST"])
@login_required
def update_device(id=None):
    try:
        device = Device.query.get(id)
        title = "Update | %r | Devices" % device.name
        if request.method == "POST":
            device.name = (
                request.form["deviceName"]
                if request.form["deviceName"]
                else device.name
            )
            device.description = (
                request.form["deviceDescription"]
                if request.form["deviceName"]
                else device.description
            )
            device.host = (
                request.form["deviceHost"].replace(" ", "")
                if request.form["deviceName"]
                else device.host
            )
            device.ssh_username = (
                request.form["deviceUser"].replace(" ", "")
                if request.form["deviceName"]
                else device.ssh_username
            )
            device.ssh_password = (
                request.form["devicePassword"]
                if request.form["deviceName"]
                else device.ssh_password
            )
            error = device.validate()
            if error:
                return render_template(
                    "devices/edit.html",
                    device=device,
                    error=error,
                    title=title,
                    current_user=current_user,
                )
            else:
                device.update()
                return redirect(url_for("devices", id=device.id))
        else:
            return render_template(
                "devices/edit.html",
                device=device,
                title=title,
                current_user=current_user,
            )
    except:
        error = "An issue was raised, IP entered might belong to an existing device"
        return render_template(
            "devices/edit.html",
            device=device,
            error=error,
            title=title,
            current_user=current_user,
        )


@app.route("/devices/<id>/delete", methods=["POST"])
@login_required
def delete_device(id=None):
    device = Device.query.get(id)
    if device:
        device.delete()
        return redirect(url_for("devices"))
    else:
        return None


@app.route("/devices/update_interfaces", methods=["POST"])
@login_required
def update_device_interfaces():
    return Device.query.get(request.get_json()["id"]).update_interfaces()


@app.route("/devices/test_connection", methods=["POST"])
def test_device_connection():
    credentials = request.get_json()
    if credentials:
        connection = Connection(
            host=credentials["host"].replace(" ", ""),
            username=credentials["ssh_username"],
            password=credentials["ssh_password"],
        )
        connection_status = connection.try_connection()
        return connection_status
    else:
        return None


"""
DEVICE INTERFACES
"""


@app.route("/interfaces/<id>", methods=["GET"])
@login_required
def interfaces(id=None):
    if id:
        interface = Interface.query.get(int(id))
        title = "%r | %r" % (interface.name, interface.device.name)
        return render_template(
            "interfaces/show.html",
            title=title,
            interface=interface,
            current_user=current_user,
        )


@app.route("/interfaces/<id>/update", methods=["GET", "POST"])
@login_required
def update_interface(id=None):
    interface = Interface.query.get(id)
    title = "Update | %r | %r" % (interface.name, interface.device.name)
    if request.method == "POST":
        interface.set(
            description=request.form["description"], bandwidth=request.form["bandwidth"]
        )

        if Policy.query.get(int(request.form["policy_id"])):
            interface.policy = Policy.query.get(int(request.form["policy_id"]))
        error = interface.validate()
        if error:
            return render_template(
                "interfaces/edit.html",
                interface=interface,
                error=error,
                title=title,
                current_user=current_user,
            )
        else:
            connection = Connection(
                host=interface.device.host,
                username=interface.device.ssh_username,
                password=interface.device.ssh_password,
            )
            connection.generate_policy_to_int(interface.policy, interface)
            if connection.check_policy_interface(interface.name, interface.policy.name) == True:
                interface.update()
                return redirect(url_for("interfaces", id=interface.id))
            else:
                return render_template(
                    "interfaces/edit.html",
                    interface=interface,
                    error="This policy is INCOMPATIBLE with this interface. Check your policy and interface settings then try again.",
                    title=title,
                    current_user=current_user,
                )
    else:
        return render_template(
            "interfaces/edit.html",
            interface=interface,
            title=title,
            policies=Policy.query.all(),
            current_user=current_user,
        )


@app.route("/interface/<id>/delete", methods=["POST"])
@login_required
def delete_interface(id=None):
    interface = Interface.query.get(id)
    if interface:
        interface.delete()
        return redirect(url_for("devices", id=interface.device.id))
    else:
        return None


"""
SERVICES VIEWS
"""


@app.route("/services/", methods=["GET"])
@app.route("/services/<id>", methods=["GET"])
@login_required
def services(id=None):
    if id:
        feedback = (
            request.args.get("feedback") if request.args.get("feedback") else None
        )
        service = Service.query.get(int(id))
        title = "%r | Services" % service.name
        return render_template(
            "services/show.html",
            title=title,
            service=service,
            feedback=feedback,
            current_user=current_user,
        )
    else:
        title = "Services"
        return render_template(
            "services/index.html",
            title=title,
            services=Service.query.all(),
            current_user=current_user,
        )


@app.route("/services/new/", methods=["GET", "POST"])
@login_required
def new_service():
    title = "New | Services"
    if request.method == "POST":
        new_service = Service(
            name=request.form["serviceName"] if request.form["serviceName"] else None,
            description=request.form["serviceDescription"]
            if request.form["serviceDescription"]
            else None,
            match_ips=request.form["serviceIps"].replace(" ", "")
            if request.form["serviceIps"]
            else None,
            match_tcp_ports=request.form["serviceTCPPorts"].replace(" ", "")
            if request.form["serviceTCPPorts"]
            else None,
            match_udp_ports=request.form["serviceUDPPorts"].replace(" ", "")
            if request.form["serviceUDPPorts"]
            else None,
            match_dscp=request.form["serviceDSCPsValues"].replace(" ", "")
            if request.form["serviceDSCPsValues"]
            else None,
            match_protocol=request.form["protocol"].replace(" ", "") if request.form["protocol"] else None
        )
        error = new_service.validate()
        if error:
            return render_template(
                "services/new.html",
                service=new_service,
                error=error,
                title=title,
                current_user=current_user,
            )
        else:
            new_service.create()
            return redirect(url_for("services", id=new_service.id))
    else:
        return render_template(
            "services/new.html",
            service=Service(),
            title=title,
            current_user=current_user,
        )


@app.route("/services/<id>/update", methods=["GET", "POST"])
@login_required
def update_service(id=None):
    service = Service.query.get(id)
    title = "Update | %r | Services" % service.name
    if request.method == "POST":
        service.name = (
            request.form["serviceName"] if request.form["serviceName"] else service.name
        )
        service.description = (
            request.form["serviceDescription"]
            if request.form["serviceDescription"]
            else service.description
        )
        service.match_ips = (
            request.form["serviceIps"].replace(" ", "")
            if request.form["serviceIps"]
            else service.match_ips
        )
        service.match_tcp_ports = (
            request.form["serviceTCPPorts"].replace(" ", "")
            if request.form["serviceTCPPorts"]
            else service.match_tcp_ports
        )
        service.match_udp_ports = (
            request.form["serviceUDPPorts"].replace(" ", "")
            if request.form["serviceUDPPorts"]
            else service.match_udp_ports
        )
        service.match_dscp = (
            request.form["serviceDSCPsValues"].replace(" ", "")
            if request.form["serviceDSCPsValues"]
            else service.match_dscp
        )
        service.match_protocol = (
            request.form["protocol"].replace(" ", "")
            if request.form["protocol"]
            else service.match_protocol
        )
        error = service.validate()
        if error:
            return render_template(
                "services/edit.html",
                service=service,
                error=error,
                title=title,
                current_user=current_user,
            )
        else:
            service.update()
            return redirect(url_for("services", id=service.id))
    else:
        return render_template(
            "services/edit.html",
            service=service,
            title=title,
            current_user=current_user,
        )


@app.route("/services/<id>/delete", methods=["POST"])
@login_required
def delete_service(id=None):
    service = Service.query.get(id)
    if service:
        service.delete()
        return redirect(url_for("services"))
    else:
        return None


"""
POLICY VIEWS
"""


@app.route("/policies/", methods=["GET"])
@app.route("/policies/<id>", methods=["GET"])
@login_required
def policies(id=None):
    if id:
        feedback = (
            request.args.get("feedback") if request.args.get("feedback") else None
        )
        policy = Policy.query.get(int(id))
        title = "%r | Policies" % policy.name
        return render_template(
            "policies/show.html",
            title=title,
            policy=policy,
            feedback=feedback,
            current_user=current_user,
        )
    else:
        title = "Policies"
        return render_template(
            "policies/index.html",
            title=title,
            policies=Policy.query.all(),
            current_user=current_user,
        )


@app.route("/policies/new/", methods=["GET", "POST"])
@login_required
def new_policy():
    title = "New | Policies"
    if request.method == "POST":
        policy = request.get_json()
        new_policy = Policy(
            name=policy["name"] if policy["name"] else None,
            description=policy["description"] if policy["description"] else None,
        )
        error = new_policy.validate()
        if error:
            return render_template(
                "policies/new.html",
                policy=new_policy,
                error=error,
                title=title,
                current_user=current_user,
            )
        else:
            new_policy.create()
            for service in policy["services"]:
                service_policy_settings = ServicePolicySettings(
                    policy_id=new_policy.id,
                    service_id=service["service_id"],
                    min_bandwidth=service["min_bandwidth"],
                    max_bandwidth=service["max_bandwidth"],
                    mark_dscp=service["mark_dscp"],
                )
                service_policy_settings.create()
            return redirect(url_for("policies", id=new_policy.id))
    else:
        return render_template(
            "policies/new.html", policy=Policy(), title=title, current_user=current_user
        )


@app.route("/policies/<id>/update", methods=["GET", "POST"])
@login_required
def update_policy(id=None):
    policy = Policy.query.get(id)
    title = "Update | %r | Policies" % policy.name
    if request.method == "POST":
        policy_data = request.get_json()
        policy.name = policy_data["name"] if policy_data["name"] else policy.name
        policy.description = (
            policy_data["description"]
            if policy_data["description"]
            else policy.description
        )

        error = policy.validate()
        if error:
            return render_template(
                "policies/edit.html",
                policy=policy,
                error=error,
                title=title,
                current_user=current_user,
            )
        else:
            policy.delete_services_settings()

            for service_settings in policy_data["services"]:
                service_policy_settings = ServicePolicySettings(
                    policy_id=policy.id,
                    service_id=service_settings["service_id"],
                    min_bandwidth=service_settings["min_bandwidth"],
                    max_bandwidth=service_settings["max_bandwidth"],
                    mark_dscp=service_settings["mark_dscp"],
                )
                service_policy_settings.create()
            policy.update()

            return redirect(url_for("policies", id=policy.id))
    else:
        return render_template(
            "policies/edit.html", policy=policy, title=title, current_user=current_user
        )


@app.route("/policies/<id>/delete", methods=["POST"])
@login_required
def delete_policy(id=None):
    policy = Policy.query.get(id)
    if policy:
        policy.delete()
        return redirect(url_for("policies"))
    else:
        return None


"""USERS VIEWS"""


@app.route("/users/", methods=["GET"])
@app.route("/users/<id>", methods=["GET"])
@login_required
def users(id=None):
    if id:
        user = User.query.get(int(id))
        title = "{}".format(user.name)
        return render_template("users/show.html", title=title, user=user,)
    else:
        return None


"""API"""

@app.route("/api/interfaces", methods=["GET"])
@app.route("/api/interfaces/<id>", methods=["GET"])
def get_interfaces(id=None):
    if Interface.query.get(id):
        interface = Interface.query.get(id)
        class_names = []
        
        since = datetime.now() - timedelta(hours=1)
        for stat in Stat.query.filter(Stat.created_on >= since, Stat.interface_id == interface.id).group_by(Stat.class_name).all():
            class_names.append(stat.class_name)

        data = {}
        for class_name in class_names:
            stats = Stat.query.filter(Stat.created_on >= since, Stat.interface_id == interface.id, Stat.class_name==class_name).order_by(-Stat.id).limit(50).all()
            stats.reverse()
            data[class_name] = {}
            data[class_name]['dates'] = []
            data[class_name]['offered_rates'] = []
            data[class_name]['drop_rates'] = []
            for stat in stats:
                data[class_name]['dates'].append(stat.created_on)
                data[class_name]['offered_rates'].append(stat.offered_rate)
                data[class_name]['drop_rates'].append(stat.drop_rate) 
        

        return jsonify({
            "id": interface.id, 
            "name": interface.name, 
            "data": data
        })
    elif id:
        return jsonify({"error": "404", "response": "Interface not found"})
    else:
        interfaces_list = []
        for interface in Interface.query.all():
            interfaces_list.append({"id": interface.id, "name": interface.name})
        return jsonify(interfaces)

@app.route("/api/services", methods=["GET"])
@app.route("/api/services/<id>", methods=["GET"])
def get_services(id=None):
    if Service.query.get(id):
        service = Service.query.get(id)

        return jsonify({"id": service.id, "name": service.name})
    elif id:
        return jsonify({"error": "404", "response": "Service not found"})
    else:
        services_list = []
        for service in Service.query.all():
            services_list.append({"id": service.id, "name": service.name})
        return jsonify(services_list)


@app.route("/api/devices/state", methods=["GET"])
@app.route("/api/devices/<id>/state", methods=["GET"])
def get_devices_state(id=None):
    if Device.query.get(id):
        device = Device.query.get(id)

        return jsonify({"id": device.id, "state": device.state})
    elif id:
        return jsonify({"error": "404", "response": "Device not found"})
    else:
        devices_state_list = []
        for device in Device.query.all():
            devices_state_list.append({"id": device.id, "state": device.state})
        return jsonify(devices_state_list)

@app.route("/api/policies", methods=["GET"])
@app.route("/api/policies/<id>", methods=["GET"])
def get_policies(id=None):
    if Policy.query.get(id):
        Policy = Policy.query.get(id)

        return jsonify({"id": policy.id, "name": policy.name})
    elif id:
        return jsonify({"error": "404", "response": "Service not found"})
    else:
        policies_list = []
        for policy in Policy.query.all():
            policies_list.append({"id": policy.id, "name": policy.name})
        return jsonify(policies_list)


@app.route("/api/interfaces/<id>/update", methods=["POST"])
def api_update_interface(id=None):
    try:
        payload = request.get_json()
        interface = Interface.query.get(id)
        interface.set(
            description=payload["description"], bandwidth=payload["bandwidth"]
        )
        policy = Policy.query.get(int(payload["policy_id"]))
        interface.policy = policy if policy else interface.policy
        error = interface.validate()
        if error:
            return jsonify(
                {
                    "status": "error",
                    "response": "Validation failed, check the new bandwidth or description",
                }
            )
        else:
            connection = Connection(
                host=interface.device.host,
                username=interface.device.ssh_username,
                password=interface.device.ssh_password,
            )
            commands = connection.generate_policy_to_int(interface.policy, interface)
            was_succesful = connection.check_policy_interface(interface.name, interface.policy.name)
            if commands and was_succesful == True:
                interface.update()
                return jsonify(
                    {
                        "status": "success",
                        "response": "The policy was applied successfuly",
                        "commands": commands,
                    }
                )
            elif commands:
                return jsonify(
                    {
                        "status": "error",
                        "response": "This policy and interface are incompatible. Check your interface and policy settings then try again",
                        "commands": commands,
                    }
                )
            else:
                return jsonify(
                    {"status": "error", "response": "The connection to the router was lost."})
    except Exception as error:
        return jsonify({"status": "error", "response": "{}".format(error)})