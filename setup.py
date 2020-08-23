from models import User, Service
from app import db


def setup_database():
    db.create_all()
    users = [
        User(name="Jania Corona", email="janiacorona@netshaping.com"),
        User(name="Ivan Ubinas", email="ivanubinas@netshaping.com"),
        User(name="Steven Sanchez", email="stevensanchez@netshaping.com"),
    ]
    for user in users:
        user.set_password("cisco")
        user.create()

    protocols = [
        "aarp",
        "appletalk",
        "arp",
        "bgp",
        "bridge",
        "bstun",
        "cdp",
        "cdp",
        "citrix",
        "clns",
        "dhcp",
        "dns",
        "egp",
        "eigrp",
        "ftp",
        "h323",
        "http",
        "icmp",
        "ip",
        "ipv6",
        "pop3",
        "rtp",
        "socks",
        "smtp",
        "sip",
        "ssh",
        "telnet",
    ]
    for protocol in protocols:
        Service(name=protocol, type="protocol", match_protocol=protocol).create()


setup_database()
