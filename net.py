from netmiko import Netmiko, NetmikoTimeoutException, NetmikoAuthenticationException
import re
from random import randint


class Connection:
    def __init__(self, host, username, password):
        self.host = host
        self.username = username
        self.password = password
        self.device_type = "cisco_ios"

    def interfaces(self):
        interfaces = {}
        for config_section in self.running_config().split("!"):
            if "interface" in config_section:
                int_name = re.search(
                    "(?<=interface )(.*?)(?=[\n\r])", config_section
                ).group(1)
                interfaces[int_name] = config_section.split("\n")
                while "" in interfaces[int_name]:
                    interfaces[int_name].remove("")
        return interfaces

    def running_config(self):
        return self.send_cmd("sh running-config")

    def stats_policy_interface(self, interface):
        stats = {}
        try:
            show = self.send_cmd("sh policy-map interface {}".format(interface)).split('\n')
            for line in show:
                if 'Service-policy output' in line:
                    policy_name = line.replace('Service-policy output: ', '').replace(' ', '')
                    stats['output_policy'] = policy_name
                    stats['classes'] = {}
                if 'Class-map:' in line:
                    class_name = line.replace('Class-map: ','').replace('(match-all)','').replace('(match-any)', '').replace(' ', '')
                    service = class_name.replace(policy_name + '-', '')
                    stats['classes'][service] = {}
                    stats['classes'][service]['class_name'] = class_name
                if 'offered rate' in line:
                    stats['classes'][service]['offered_rate'] = re.search("offered rate (.*?) bps", line).group(1).replace(" ", "")
                    stats['classes'][service]['drop_rate'] = re.search("drop rate (.*?) bps", line).group(1).replace(" ", "")
            stats['success'] = True
        except:
            stats['success'] = False
        return stats

    def create_acl(self, acl_name, source_ip):
        return self.send_config_cmds(
            [
                "ip access-list extended {}".format(acl_name),
                "permit ip host {} any".format(source_ip),
            ]
        )

    def shutdown_int(self, interface):
        return self.send_config_cmds(["interface {}".format(interface), "shutdown"])

    def no_shutdown_int(self, interface):
        return self.send_config_cmds(["interface {}".format(interface), "no shutdown"])

    def set_ip_int(self, ip, mask, interface):
        return self.send_config_cmds(
            ["interface {}".format(interface), "ip address {} {}".format(ip, mask)]
        )

    def no_ip_int(self, interface):
        return self.send_config_cmds(
            ["interface {}".format(interface), "no ip address"]
        )

    def set_hostname(self, hostname):
        return self.send_config_cmds(["hostname {}".format(hostname)])

    def class_match_protocol(self, class_name, protocol):
        return self.send_config_cmds(
            [
                "class-map match-all {}".format(class_name),
                "match protocol {}".format(protocol),
            ]
        )

    def class_match_dscp(self, class_name, dscp_value):
        return self.send_config_cmds(
            [
                "class-map match-all {}".format(class_name),
                "match ip dscp {}".format(dscp_value),
            ]
        )

    def unset_policy_setting(self, policy_name, classes):
        if type(classes) is not list:
            raise TypeError("Argument classes should be of list type")

        commands = ["policy-map {}".format(policy_name)]
        for _class in classes:
            commands.append("class {}".format(_class["name"]))
            if _class["bandwith"] != None:
                commands.append("no bandwith {}".format(_class["bandwith"]))
            if _class["priority"] != None:
                commands.append("no priority {}".format(_class["priority"]))
            if _class["dscp"] != None:
                commands.append("no set ip dscp {}")
        return self.send_config_cmds(commands)

    def set_policy_setting(self, policy_name, classes):
        """
        Argument 'classes' is a list of dictionaries where every dict represents
        a class with its Quality of Service settings. Example:
        classes = [{    'name': example,
                        'bandwith': None,
                        'priority': None
                        'dscp': None
                    }, ...]
        """
        if type(classes) is not list:
            raise TypeError("Argument classes should be of list type")

        commands = ["policy-map {}".format(policy_name)]
        for _class in classes:
            commands.append("class {}".format(_class["name"]))
            if _class["bandwith"] != None:
                commands.append("bandwith {}".format(_class["bandwith"]))
            if _class["priority"] != None:
                commands.append("priority {}".format(_class["priority"]))
            if _class["dscp"] != None:
                commands.append("set ip dscp {}")
        return self.send_config_cmds(commands)

    def apply_policy_to_int(self, policy_name, interface, type):
        return self.send_config_cmds(
            [
                "interface {}".format(interface),
                "service-policy {} {}".format(type, policy_name),
                "load-interval 30"
            ]
        )

    def get_current_policy_name(self, interface_name, type="output"):
        interface_settings = self.interfaces()[interface_name]
        string_match = "service-policy {}".format(type)
        for setting in interface_settings:
            if string_match in setting:
                policy_name = setting.replace(string_match, "").replace(" ", "")
                return policy_name
        return None

    def generate_policy_to_int(self, policy, interface, type="output"):
        try:
            commands = []
            description = "Dynamic Generated by Netshaping for Policy: {}".format(
                policy.name
            )

            for service_settings in policy.services:
                service = service_settings.service
                class_name = _generate_class_name(policy.name, service.name)
                
                if service.match_ips:
                    access_list_name = _generate_acl_name(service.name)
                    commands.append(
                        "ip access-list extended {}".format(access_list_name)
                    )
                    for ip in service.match_ips.split(","):
                        if service.match_tcp_ports or service.match_udp_ports:
                            if service.match_tcp_ports:
                                commands.append(
                                    "permit tcp host {} any eq {}".format(
                                        _no_spaces(ip),
                                        _ip_list_to_str(service.match_tcp_ports),
                                    )
                                )
                            if service.match_udp_ports:
                                commands.append(
                                    "permit udp host {} any eq {}".format(
                                        _no_spaces(ip),
                                        _ip_list_to_str(service.match_udp_ports),
                                    )
                                )
                        else:
                            commands.append("permit ip host {} any".format(ip))
                commands.append("class-map match-all {}".format(class_name))
                if service.match_protocol:
                    commands.append("match protocol {}".format(service.match_protocol))
                if service.match_ips:
                    commands.append(
                        "match access-group name {}".format(access_list_name)
                    )
                if service.match_dscp:
                    for dscp in service.match_dscp.split(","):
                        commands.append("match dscp {}".format(_no_spaces(dscp)))
                commands.append(
                    "policy-map {}".format(_generate_policy_name(policy.name))
                )
                commands.append("class {}".format(class_name))
                if service_settings.min_bandwidth:
                    commands.append(
                        "bandwidth {}".format(service_settings.min_bandwidth)
                    )
                if service_settings.max_bandwidth:
                    commands.append(
                        "shape average {}".format(service_settings.max_bandwidth)
                    )
                if service_settings.mark_dscp:
                    commands.append("set dscp {}".format(service_settings.mark_dscp))

            commands.append("interface {}".format(interface.name))
            commands.append("bandwidth {}".format(interface.bandwidth))
            commands.append("load-interval 30")
            current_policy_name = self.get_current_policy_name(
                interface.name, type=type
            )
            if current_policy_name:
                commands.append(
                    "no service-policy {} {}".format(type, current_policy_name)
                )
            commands.append(
                "service-policy {} {}".format(type, _generate_policy_name(policy.name))
            )
            self.send_config_cmds(commands)
            return commands
        except:
            return None

    def check_policy_interface(self, interface_name, policy_name):
        try:
            for config_line in self.interfaces()[interface_name]:
                if policy_name in config_line:
                    return True
        finally:
            return False

    def send_config_cmds(self, commands):
        try:
            connection = Netmiko(
                host=self.host,
                username=self.username,
                password=self.password,
                device_type=self.device_type,
                timeout=150,
            )
            response = connection.send_config_set(commands)
            connection.disconnect()
            return response
        except NetmikoAuthenticationException:
            return "failed authentication"
        except:
            return "timeout"

    def try_connection(self):
        try:
            connection = Netmiko(
                host=self.host,
                username=self.username,
                password=self.password,
                device_type=self.device_type,
                timeout=10,
            )
            connection.disconnect()
            return "success"
        except NetmikoAuthenticationException:
            return "failed_authentication"
        except:
            return "timeout"

    def send_cmd(self, command):
        try:
            connection = Netmiko(
                host=self.host,
                username=self.username,
                password=self.password,
                device_type=self.device_type,
                timeout=20,
            )
            response = connection.send_command(command)
            connection.disconnect()
            return response
        except NetmikoAuthenticationException:
            return "failed_authentication"
        except:
            return "timeout"

def _ip_list_to_str(ip_list):
    return str(ip_list).replace("[", "").replace("]", "").replace(",", " ")


def _generate_class_name(policy_name, service_name):
    return "D-{}-{}".format(policy_name.replace(" ", ""), service_name.replace(" ", ""))


def _generate_acl_name(service_name):
    return "D-{}".format(service_name.replace(" ", ""))


def _generate_policy_name(policy_name):
    return "D-{}".format(policy_name.replace(" ", ""))


def _no_spaces(text):
    return "{}".format(text.replace(" ", ""))
